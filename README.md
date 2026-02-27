Minimize: f(x), $x\in \mathbb{R}^n$ 

Subject to: $g_i(x) ≤ 0$ & $h_j(x) == 0$

At iteration t, we maintain a population: $\{x_i^t\}_{i=1}^{N(t)}$ 

Each candidtate has:
- Objective value $f_i^t$ 
- Constraint violation measure $v_i^t$

Proceeding until a fixed evolution budget is exhausted (termination is based on computational effort)

### Constraint Handeling:
total voilation $\implies$ $v(x) = \frac{1}{m}(\sum_i max(0, g_i(x)) + \sum_j|h_j(x)|_\epsilon)$

2 relaxation params:
- $\epsilon_{f}$: objective relaxation
- $\epsilon$: constraint relaxation
> Selection uses a dynamic $\epsilon$ constrained dominance rule with an auxiliary objective relaxation threshold $\epsilon_{f}$.
> If constraint violation ≤ $\epsilon \rightarrow$ treat as feasible
> If constraint value ≤ $\epsilon_f \rightarrow$ treat as acceptable in objective cmp (even if infeasible)

Selection rules: 

equality constraints treated as inequalities with some tolerance 

Selection b/w candidates x and y follows as:
1. If both are $\epsilon$ feasible $\rightarrow$ compare objective
2. If 1 is feasible $\rightarrow$ feasible one wins
3. If both infesible $\rightarrow$ cmp voilation magnitude 

$\epsilon$ & $\epsilon_f$ decreases over time, acting like continuation scheme
- Early stage tolerates infeasibility
- Late stage enforces strict feasibility

### Search: DE
For each target vector $x_i$, trial vector is constructed as stochastic linear combination of other population members.

**2 mutation stratergies used:**
1. $x_{trial}​=x_i​+F(x_{r1}​−x_i​)+F_2​(x_{r2}​−x_{r3}​)$ here, $x_{r1}$ is choosen from top p% of poplulation (similar to JADE `r1 selected from top ranked subset of population`)
using population differences as search drxn. $\implies$ population geometery substitute for gradient info
2. Rank Based: 3 candidates are ranked by fitness (best, medium, worst)
$x_{trial}​=x_i​+F(x_{best}​−x_i​)+F(x_{medium}​−x_{worst}​)$
    
    - Introducing exploitation toward high-quality sols while preserving diversity
    - [adaptively choosing b/w these operators based on observed performance](#adaptive-operator-probability-update)

> Boundary violations are handled by avg the trial value with the violated bound. $x_j = \frac{x_j + bounds}{2}$

**Crossover:** Binomial similar to what is already there is others so we can avoid it

**Perturbation:**
when crossover doesn't modify coordinate:

$x_j = Couchy(x_j, 0.1)\ with\ prob\ 0.2$ 

$x_j = x_j\ \ otherwise$

injecting rare large jumps to prevent coordinate stagnation


### Param control: (similar to SHADE)
- mutation scale F and crossover rate CR is not fixed.
- successful param values are stored & updated using weighted Lehmer mean: $F_{new} = \frac{\sum w_i F_i^2}{\sum w_i F_i}$
- weights proportional to achieved improvement

### Circular Elitist Update
successful offspring inserted into elite front using rotating idx:

$PFIndex=(PFIndex+1)\ mod\ N(t)$

to ensure uniform elitist injection.


### Population size  && selection mechanism
population size decreases gradually over time (deterministic scheduling) $N(t)$ = linear interpolation from $N_{init}$​ to 4
- early phase: larg population $\rightarrow$ exploration
- late phase: small population $\rightarrow$ exploitation

- selection is elitist
- successful trials are inserted into elite front and inferior individuals are later removed via truncation.
- ff too many candidates accumulate, population is truncated based on penalized fitness ranking
- No explicit diversity preservation beyond mutation structure

> Conclusion:
> 1. Doesn't keep external archive(JADE, L-SHADE, UDE-III)


------------
------------


#### Adaptive Operator Probability Update
- total improvement produced by EB operator (EB mode is when alternative mutation apprears)
- total improvement produced by standard operator
$p_{EB} = \frac{\Delta_{EB}}{\Delta_{EB} + \Delta_{standard}}$
> Probability of using  EB mutation strategy is updated proportionally to its recent fitness improvement contribution

--------------
## Acknowledgments
This project incorporates and modifies code from:
https://github.com/SichenTao/IEEE-CEC-2025-Competition-RDEx/tree/main; https://github.com/P-N-Suganthan/CEC2017
