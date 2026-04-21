#!/usr/bin/env python3
"""
Given m algos with n trials each on k problems.
Per problem, perform mn(mn-1)/2 pairwise comparisons among all trials.

Accuracy score A (per trial, per problem):
  - both feasible         -> lower Min_EV gets 1.0 (0.5 each if tie)
  - both infeasible       -> lower LCV gets 1.0 (0.5 each if tie)
  - one feas, one infeas  -> feasible gets 1.0

Speed score S (per trial, per problem):
  Compare trial X vs Y. Let:
    ft_X = first FE at which X reached *threshold* T
    ft_Y = first FE at which Y reached T
  where T is the "worse" of the two final values:
    - both feasible         -> T = max(EV_X_final, EV_Y_final); lookup in EV trajectory
    - both infeasible       -> T = max(LCV_X_final, LCV_Y_final); lookup in LCV trajectory
    - one feasible          -> T = LCV of infeasible; lookup in LCV trajectory for both
  Faster trial gets 1.0; tie = 0.5 each.

Algorithm problem score = A_algo + S_algo (summed over all its trials).
Algorithm total score = sum over all 28 problems.

Feasibility: a trial is feasible at a given sampling point if max violation <= FEAS_TOL.
  - Inequality g_i: max(0, g_i)
  - Equality   h_j: max(0, |h_j| - EQ_DELTA)  (EQ_DELTA = 1e-4 per CEC spec)

Precision cutoff: Min_EV < 1e-8 recorded as 0 (handled downstream).
"""

import sys
import os
import glob

NG = list(map(int, "1 1 1 2 2 0 0 0 1 0 1 2 3 1 1 1 1 2 2 2 2 3 1 1 1 1 2 2".split()))
NH = list(map(int, "0 0 1 0 0 6 2 2 1 2 1 0 0 1 1 1 1 1 0 0 0 0 1 1 1 1 1 0".split()))
RES = 2001
FEAS_TOL = 1e-4
EQ_DELTA = 1e-4
D = 30
MAX_FES = 20000 * D
# Sampling points: indices 0..2000, FE at index k = k * 10 * D  (FE[0]=0 init, FE[2000]=MAX_FES)
FE_AT = [k * 10 * D for k in range(RES)]


def load_trial_trajectories(prefix, dir_, f, run_idx=0):
    """Return (ev_traj, lcv_traj, feas_traj) each of length RES, for one trial.

    ev_traj[k]   = Min_EV at sampling point k
    lcv_traj[k]  = max-violation (CEC LCV proxy, using max not min across pop -- see note)
    feas_traj[k] = bool, lcv_traj[k] <= FEAS_TOL
    """
    # EV file: one line per run, RES values
    with open(f"{dir_}/{prefix}_F{f}_D{D}.txt") as fh:
        lines = [ln for ln in fh if ln.strip()]
    ev_line = lines[run_idx].split()
    # File has RES values; last entry is sentinel NFEval (not an EV), first RES-1 are EV trajectory
    # Using the first RES-1 as the EV trajectory sampling; repeat last for symmetry
    ev_traj = [float(x) for x in ev_line[:RES - 1]]
    ev_traj.append(ev_traj[-1])  # pad to length RES

    # Constraint file: per run, one line with RES * (ng+nh) values
    ng, nh = NG[f - 1], NH[f - 1]
    m = ng + nh
    if m == 0:
        lcv_traj = [0.0] * RES
        feas_traj = [True] * RES
        return ev_traj, lcv_traj, feas_traj

    with open(f"{dir_}/{prefix}_C2_F{f}_D{D}.txt") as fh:
        clines = [ln for ln in fh if ln.strip()]
    craw = [float(x) for x in clines[run_idx].split()]

    lcv_traj = []
    feas_traj = []
    for k in range(RES):
        base = k * m
        if base + m > len(craw):
            # missing tail: repeat last valid
            lcv_traj.append(lcv_traj[-1] if lcv_traj else 0.0)
            feas_traj.append(feas_traj[-1] if feas_traj else True)
            continue
        max_v = 0.0
        for j in range(ng):
            max_v = max(max_v, max(0.0, craw[base + j]))
        for j in range(nh):
            v = max(0.0, abs(craw[base + ng + j]) - EQ_DELTA)
            max_v = max(max_v, v)
        lcv_traj.append(max_v)
        feas_traj.append(max_v <= FEAS_TOL)
    return ev_traj, lcv_traj, feas_traj


def first_fe_reaching_ev(ev_traj, threshold):
    """Return FE at first sample where ev_traj[k] <= threshold, else MAX_FES+1."""
    for k in range(RES):
        if ev_traj[k] <= threshold + 1e-12:
            return FE_AT[k]
    return MAX_FES + 1


def first_fe_reaching_lcv(lcv_traj, threshold):
    for k in range(RES):
        if lcv_traj[k] <= threshold + 1e-12:
            return FE_AT[k]
    return MAX_FES + 1


def compare_trials(TX, TY):
    """Return (aX, aY, sX, sY) points. Each 0/0.5/1 summing to 1 per category."""
    evX, lcvX, feasX_all = TX
    evY, lcvY, feasY_all = TY
    fX_final = evX[-1]
    fY_final = evY[-1]
    vX_final = lcvX[-1]
    vY_final = lcvY[-1]
    feasX = feasX_all[-1]
    feasY = feasY_all[-1]

    # ---- Accuracy ----
    if feasX and feasY:
        if abs(fX_final - fY_final) < 1e-10:
            aX = aY = 0.5
        elif fX_final < fY_final:
            aX, aY = 1.0, 0.0
        else:
            aX, aY = 0.0, 1.0
    elif feasX and not feasY:
        aX, aY = 1.0, 0.0
    elif feasY and not feasX:
        aX, aY = 0.0, 1.0
    else:
        if abs(vX_final - vY_final) < 1e-12:
            aX = aY = 0.5
        elif vX_final < vY_final:
            aX, aY = 1.0, 0.0
        else:
            aX, aY = 0.0, 1.0

    # ---- Speed ----
    if feasX and feasY:
        T = max(fX_final, fY_final)
        fe_X = first_fe_reaching_ev(evX, T)
        fe_Y = first_fe_reaching_ev(evY, T)
    elif not feasX and not feasY:
        T = max(vX_final, vY_final)
        fe_X = first_fe_reaching_lcv(lcvX, T)
        fe_Y = first_fe_reaching_lcv(lcvY, T)
    else:
        # mixed: threshold = LCV of infeasible trial; both must reach that LCV
        if not feasX:
            T = vX_final
        else:
            T = vY_final
        fe_X = first_fe_reaching_lcv(lcvX, T)
        fe_Y = first_fe_reaching_lcv(lcvY, T)

    if fe_X == fe_Y:
        sX = sY = 0.5
    elif fe_X < fe_Y:
        sX, sY = 1.0, 0.0
    else:
        sX, sY = 0.0, 1.0

    return aX, aY, sX, sY


def load_all_trials(prefix, dir_, f):
    """Return list of trials (one per run). n = number of non-empty lines."""
    with open(f"{dir_}/{prefix}_F{f}_D{D}.txt") as fh:
        n_ev = sum(1 for ln in fh if ln.strip())
    with open(f"{dir_}/{prefix}_C2_F{f}_D{D}.txt") as fh:
        n_c = sum(1 for ln in fh if ln.strip())
    ng, nh = NG[f - 1], NH[f - 1]
    if ng + nh == 0:
        n = n_ev
    else:
        n = min(n_ev, n_c)
    return [load_trial_trajectories(prefix, dir_, f, run_idx=i) for i in range(n)]


def score_problem(trialsA, trialsB):
    """Return (A_A, A_B, S_A, S_B) summed across mn(mn-1)/2 comparisons."""
    AA = AB = SA = SB = 0.0
    nA, nB = len(trialsA), len(trialsB)
    # trial-trial among all combined trials (A vs A, A vs B, B vs B)
    all_trials = [(t, 'A') for t in trialsA] + [(t, 'B') for t in trialsB]
    mn = len(all_trials)
    for i in range(mn):
        for j in range(i + 1, mn):
            TX, labX = all_trials[i]
            TY, labY = all_trials[j]
            aX, aY, sX, sY = compare_trials(TX, TY)
            if labX == 'A':
                AA += aX; SA += sX
            else:
                AB += aX; SB += sX
            if labY == 'A':
                AA += aY; SA += sY
            else:
                AB += aY; SB += sY
    return AA, AB, SA, SB


def main():
    if len(sys.argv) < 5:
        print("usage: score_cec2026.py <prefixA> <dirA> <prefixB> <dirB>")
        sys.exit(1)
    pA, dA, pB, dB = sys.argv[1:5]
    print(f"{'F':>3}  {'A_acc':>7} {'B_acc':>7}  {'A_spd':>7} {'B_spd':>7}  "
          f"{'A_tot':>7} {'B_tot':>7}")
    totAA = totAB = totSA = totSB = 0.0
    for f in range(1, 29):
        try:
            trialsA = load_all_trials(pA, dA, f)
            trialsB = load_all_trials(pB, dB, f)
        except FileNotFoundError as e:
            print(f"F{f:02d}: missing file -> {e}")
            continue
        AA, AB, SA, SB = score_problem(trialsA, trialsB)
        totAA += AA; totAB += AB; totSA += SA; totSB += SB
        print(f"F{f:02d}  {AA:>7.2f} {AB:>7.2f}  {SA:>7.2f} {SB:>7.2f}  "
              f"{AA + SA:>7.2f} {AB + SB:>7.2f}")
    print("-" * 60)
    print(f"SUM  {totAA:>7.2f} {totAB:>7.2f}  {totSA:>7.2f} {totSB:>7.2f}  "
          f"{totAA + totSA:>7.2f} {totAB + totSB:>7.2f}")
    better = "B" if (totAB + totSB) > (totAA + totSA) else ("A" if (totAA + totSA) > (totAB + totSB) else "TIE")
    print(f"\nCEC-2026 total: A={totAA + totSA:.2f}  B={totAB + totSB:.2f}  ->  better: {better}")


if __name__ == "__main__":
    main()
