#!/usr/bin/env python3
"""
Default usage:
  uv run plot_speed.py

Custom usage:
  uv run plot_speed.py \
    --prefix-a RDEx \
    --dir-a "RDEx Results in 25 runs" \
    --prefix-b RDEx_improv \
    --dir-b "Results RDEx_new" \
    --csv-out speed_25runs_rdex_vs_improv.csv \
    --png-out speed_25runs_rdex_vs_improv.png
"""

from __future__ import annotations

import argparse
import csv
import re
import subprocess
from pathlib import Path

import matplotlib.pyplot as plt


ROW_RE = re.compile(
    r"^F(\d{2})\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s*$"
)


def run_score(score_script: Path, prefix_a: str, dir_a: Path, prefix_b: str, dir_b: Path) -> str:
    cmd = [
        "python3",
        str(score_script),
        prefix_a,
        str(dir_a),
        prefix_b,
        str(dir_b),
    ]
    proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return proc.stdout


def parse_speed_rows(score_stdout: str) -> list[tuple[int, float, float]]:
    rows: list[tuple[int, float, float]] = []
    for line in score_stdout.splitlines():
        m = ROW_RE.match(line)
        if not m:
            continue
        func = int(m.group(1))
        a_spd = float(m.group(4))
        b_spd = float(m.group(5))
        rows.append((func, a_spd, b_spd))
    if len(rows) != 28:
        raise ValueError(f"Expected 28 function rows, found {len(rows)}.")
    rows.sort(key=lambda x: x[0])
    return rows


def write_csv(rows: list[tuple[int, float, float]], csv_out: Path) -> None:
    with csv_out.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["function", "RDEx_speed", "RDEx_improv_speed"])
        w.writerows(rows)


def write_plot(
    rows: list[tuple[int, float, float]],
    png_out: Path,
    label_a: str,
    label_b: str,
) -> None:
    x = [r[0] for r in rows]
    a = [r[1] for r in rows]
    b = [r[2] for r in rows]

    plt.figure(figsize=(12, 4.5))
    plt.plot(x, a, marker="o", label=f"{label_a} speed score")
    plt.plot(x, b, marker="X", label=f"{label_b} speed score")
    plt.xticks(range(1, 29))
    plt.xlabel("Functions (F1-F28)")
    plt.ylabel("Speed score")
    plt.title(f"Speed comparison: {label_a} vs {label_b} (25 runs)")
    plt.grid(alpha=0.25)
    plt.legend()
    plt.tight_layout()
    plt.savefig(png_out, dpi=160)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create speed CSV + plot from score_cec2026.py output.")
    parser.add_argument("--prefix-a", default="RDEx")
    parser.add_argument("--dir-a", default="RDEx Results in 25 runs")
    parser.add_argument("--prefix-b", default="RDEx_improv")
    parser.add_argument("--dir-b", default="Results RDEx_new")
    parser.add_argument("--score-script", default="score_cec2026.py")
    parser.add_argument("--csv-out", default="speed_25runs_rdex_vs_improv.csv")
    parser.add_argument("--png-out", default="speed_25runs_rdex_vs_improv.png")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    score_script = (root / args.score_script).resolve()
    dir_a = (root / args.dir_a).resolve()
    dir_b = (root / args.dir_b).resolve()
    csv_out = (root / args.csv_out).resolve()
    png_out = (root / args.png_out).resolve()

    stdout = run_score(score_script, args.prefix_a, dir_a, args.prefix_b, dir_b)
    rows = parse_speed_rows(stdout)
    write_csv(rows, csv_out)
    write_plot(rows, png_out, args.prefix_a, args.prefix_b)

    sum_a = sum(r[1] for r in rows)
    sum_b = sum(r[2] for r in rows)
    print(f"Wrote CSV: {csv_out}")
    print(f"Wrote PNG: {png_out}")
    print(f"Speed sums -> {args.prefix_a}: {sum_a:.2f}, {args.prefix_b}: {sum_b:.2f}")


if __name__ == "__main__":
    main()

