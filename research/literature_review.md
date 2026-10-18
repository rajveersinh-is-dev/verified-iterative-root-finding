# Literature review

## Search strategy
Searched (via web) for: "fourth order iterative methods nonlinear equations",
"Kung Traub optimal order", "Newton method convergence order Taylor",
and related. Also consulted standard texts (Stoer & Bulirsch 2002) and
the Kung--Traub (1974) paper.

## Principal sources
1. Kung, H. T. and Traub, J. F. (1974). Optimal order of one-point and
   multipoint iteration. J. ACM 21(4), 643--651. (Verified via ACM/Crossref.)
2. Stoer, J. and Bulirsch, R. (2002). Introduction to Numerical Analysis,
   3rd ed., Springer. (Verified via Springer.)
3. Traub, J. F. (1964). Iterative Methods for the Solution of Equations,
   Prentice-Hall.

## Related work
A large literature constructs fourth-order methods using weight functions,
frozen derivatives, and Jarratt-type steps (e.g., Chun 2005 and many
recent variants). These typically require two or three function/derivative
evaluations and satisfy the Kung--Traub bound.

## Comparison table
| Source | Method family | Evaluations/step | Order | Relation to present work |
|---|---|---|---|---|
| Kung--Traub 1974 | multipoint | 3 evals | 4 (optimal) | Theoretical bound we aim to meet |
| Newton | one-point | 1 f + 1 f' | 2 | Baseline |
| Secant | multipoint | 2 f | ~1.618 | Baseline (derivative-free) |
| Present M4 | two-step | 1 f + 1 f' | 4 | Specific rational correction |

## Novelty assessment
The proposed M4 is a specific instance of the broad family of two-step
fourth-order methods. We do not claim it is the first or optimal in any
global sense; the contribution is a clean, self-contained derivation,
symbolic verification, open implementation, and reproducible experiments.
Saturation of the field means the novelty is incremental at best.

## Limits of search
Literature search was performed in a single session and is not exhaustive.
Equivalent formulations of (1) may exist under different names. Absence of
an identical formula in the searched sources does not prove originality.
