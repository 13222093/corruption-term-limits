# METRICS.md (pre-registered before any extension experiment)

Committed before running E1-E7. Any later change is logged at the bottom with a reason.

## 0. Notation
State z(t) = (x1, x2, x3, x4, y): frequencies of OC, PC, OD, PD and the honest umpire fraction y.
Time: mean field in model time units (one strategy revision per individual per unit time);
IBM in generations (each individual revises once per generation on average).

## 1. Primary metrics

| ID | Name | Definition |
|---|---|---|
| M1 | Time-averaged honesty | ybar = mean of y(t) over the averaging window |
| M2 | Cooperation measure | C(t) = x1 + x2 (frequency of cooperator strategies, as "All cooperators" in Lee et al. Fig. 3D); Cbar = window mean |
| M2b | Realized cooperation | R(t) = x1 [y (1 - x4) + (1 - y)(1 - x2)] + x2 y (1 - x4): expected number of donations made per player per game, accounting for drop-outs (PD leaves honest umpires, PC leaves corrupt ones); Rbar = window mean |
| M2c | Mean player payoff | W(t) = x . Q(y) x; Wbar = window mean |
| M3 | Cycle amplitude | Mean field: A_y = max y - min y over the window. IBM: A_y = q95(y) - q05(y) of the recorded y in the window. Same for C (A_C) |
| M4 | Minimum cooperation | Mean field: C_min = min C over the window. IBM: C_q05 = 5th percentile of C (robust); absolute min also stored |
| M5 | Corruption episode | Maximal interval with y(t) < theta, theta = 0.5 (majority corrupt). IBM: gaps shorter than 5 generations between sub-threshold intervals are merged; intervals shorter than 5 generations are discarded. Mean field: no merging needed (deterministic) |
| M5a | Episode depth (honesty) | D_y = 1 - min y within the episode (peak corruption) |
| M5b | Episode depth (cooperation) | D_C = min C within the episode (cooperation trough; lower = deeper) |
| M5c | Episode frequency | number of episodes per 1000 time units |
| M6 | Recovery time | episode duration: time from y falling below theta to y returning to theta or above |
| M7 | Vigilance | x2bar = window mean of PC frequency |
| M8 | Corrupt-majority time | fraction of window with y < theta |

## 2. Mean-field protocol
- Solver: scipy solve_ivp, LSODA, rtol = 1e-9, atol = 1e-11 (R4 check: rtol = 1e-10, atol = 1e-12
  and DOP853 on a sub-sample must change M1, M3, M4 by less than 1e-4 absolute, except within 1e-3
  of a bifurcation).
- Initial state: Fig. 3 start (y = 1, x = (0.1, 0.4, 0.4, 0.1)) unless stated.
- Burn-in: t_burn = 10000. Averaging window T_w = 10000, sampled every 0.5 time units.
  At mu = nu = 0.001 (E7 robustness; period about 1100): t_burn = T_w = 40000.
- Attractor classification: equilibrium if A_y < 1e-6 over the window; otherwise cycle. Periodic
  if the last 5 successive maxima of y agree within 1e-4; period = mean spacing of those maxima.
- Local stability (R2): interior equilibrium found by root finding (hybr, tol 1e-12) and
  continued in the parameter; stable if all eigenvalues of the symbolic Jacobian (reduced
  coordinates x1, x2, x3, y) have negative real part. Hopf point: sign change of the real part of
  the leading complex pair, refined by Brent's method (xtol 1e-10).
- Bistability (H5): two initial states, "honest start" (y = 0.99, x = (0.97, 0.01, 0.01, 0.01))
  and "corrupt start" (y = 0.01, x = (0.01, 0.73, 0.25, 0.01), near fixed point 10). Bistable if
  the window means ybar differ by more than 0.05. Also: count of stable equilibria found by root
  finding from 60 random starts.
- Hysteresis (H5): sweep kappa up from 0 to 1 and then down, each step starting from the end
  state of the previous step (burn-in 5000, window 5000). Hysteresis if up and down branches of
  ybar differ by more than 0.05 at some kappa.
- Delay stability (H6): characteristic roots of the linearized DDE by Chebyshev collocation of
  the infinitesimal generator (n = 40 nodes; checked at n = 80). Stable if the rightmost root has
  negative real part. Confirmed by DDE simulation (method of steps on solve_ivp dense output) at
  selected points.

## 3. IBM protocol
- Settings: small (M = 50, N = 10, mu = 0.001, nu = 0.005, s = 1e10) and large (M = 5000,
  N = 1000, mu = 0.01, nu = 0.05, s = 0.3), from Lee et al. Fig. 1.
- Initial state: all OD, all umpires honest (as in Fig. 1C, D).
- Burn-in: small 5000 generations, large 1000 generations. Window: small 1e5 generations, large
  5000 generations (quick profile: 1/5 of these). State recorded every 0.5 generation (small) or
  1 generation (large).
- Replicates: n = 30 independent seeds per condition (full), 8 (quick). Justified by a
  standard-error convergence check at the base condition (SE of M1 vs n = 5, 10, 20, 30, 50).
- Summary: replicate-level metrics; mean and 95% bootstrap percentile CI (10000 resamples).
  Episode-level metrics (depth, duration) are first averaged within a replicate, then across
  replicates (replicates with no episode are excluded from that metric and counted).
- Stationarity check: M1 at window 1e5 vs 2e5 generations (small) must agree within the CI.
- Finite size: M in {50, 100, 200, 400} with N = M/5 and fixed per-individual rates.

## 4. Hypothesis decision rules (fixed in advance)
- H1 supported if, in mean field, ybar increases and A_y decreases (weakly, to 0 past any Hopf
  point) with rho over the tested range, AND in the IBM ybar(rho) > ybar(0) and episode frequency
  decreases, with non-overlapping 95% CIs at the largest rho. Mixed if only one of honesty or
  damping holds or only one level of description agrees.
- H2 supported if, with rising rho, x2bar declines AND the mean episode depth (D_y or D_C) of
  the remaining episodes increases, with non-overlapping CIs between rho = 0 and some rho > 0
  that still has episodes in at least half the replicates. Not supported if depth decreases or
  does not change. Mixed if only one depth measure or only one setting shows it.
- H3: mean field: supported for V1 if dybar/dkappa < 0 at fixed rho (expected analytically).
  Beyond mean field: compare IBM V1(rho, kappa) with V0(rho (1 - kappa)); the equivalence "holds"
  if the difference in ybar has a 95% CI containing 0 at all tested points; "breaks" otherwise.
  For V2 and V3, supported if ybar decreases with kappa at fixed rho.
- H4: with Delta(rho, h) = ybar(rho, h) - ybar(0, h): substitutes if Delta increases with h
  (rotation helps more where transparency is costly) on at least 75% of grid pairs; complements
  if Delta decreases with h on at least 75%; mixed otherwise. Same rule repeated for Cbar.
- H5 supported if bistability (Section 2) is found on an open region of (rho, kappa) AND a
  hysteresis loop exists in a kappa sweep. Not supported if neither.
- H6 supported if at kappa >= 0.5 there exist (rho, T_lag) where the V3 equilibrium is unstable
  while the V1 equilibrium at the same (rho, kappa) is stable. Not supported if delay never
  removes stability. Mixed if destabilization occurs only for T_lag far from one term (1/rho).

## 5. Change log
(none yet)
