# PROGRESS.md

Log of completed tasks: what was done, results, next step. Newest entries at the bottom.

## 2026-10-10 Phase 0: setup and specification
- Read CLAUDE.md and all four PDFs in refs/. The PNAS paper is a scanned image PDF; read visually
  at 150-300 dpi (payoff matrices, equations, transition matrix, figure captions).
- SI Appendix could not be obtained (PMC CAPTCHA, PNAS 403, IIASA bot protection). Proceeding per
  integrity rule 1; SI-dependent items marked UNVERIFIED in SPEC.md.
- Found that the Q(y) weighting typo is in the PDF itself (not only PMC). Resolved (D-001).
- Found two inconsistencies in the printed rare-exploration matrix T (rows 3 and 4) that sit in
  transient rows (SPEC D4, D5) and one text-vs-figure inconsistency in the Fig. 3 caption (D3).
- Inequality 4 confirmed as h < sqrt(f (f + B)); s = 10^10 confirmed.
- Environment: Python 3.12.8, numba 0.68.0 installed with pip; MiKTeX 25.12 installed with winget
  (pdflatex works); mingw32-make for the Makefile.
- Wrote PLAN.md, SPEC.md, DECISIONS.md (D-001 to D-012).
- Next: Phase 1 payoffs.

## 2026-10-10 Phase 1: payoffs
- src/params.py (parameters, inequalities), src/payoffs.py (Q_H, Q_C, Q(y), umpire income,
  rule-based single game, finite-population payoffs).
- tests/test_payoffs.py: 21 tests pass. Matrices equal the rule-based game for all 16 pairs and
  both umpire types (3 parameter sets); printed signs checked symbolically; brute-force pair
  enumeration of umpire income equals the printed P_H - P_C at 200 random states per parameter
  set; sympy identity check; finite-population payoffs checked by exact enumeration in a tiny
  population and converge to the infinite-population values.
- Next: Phase 2 replicator-mutator ODE.

## 2026-10-10 Phase 2: replicator-mutator ODE
- src/replicator_mutator.py (numba right-hand sides: published equations and the exact mean field
  of the Fermi IBM), src/analysis.py (sympy Jacobian, equilibria, continuation, folds, Hopf,
  DDE characteristic roots).
- Numerical issue found and fixed: with negative mean payoff the simplex S = 1 is unstable for
  the replicator equation written in unnormalized form; round-off grew and LSODA failed. Payoffs
  are now evaluated at x / S, which conserves S exactly and is identical on the simplex.
- B1 reproduced: y = 0 gives x -> (0, 0.75, 0.25, 0) from random starts (OD = h/(f+B) = 0.25).
  B2 reproduced: y = 1 gives OC -> 1. The printed Q(y) weighting fails B1 (test).
- Orbit shrinkage reproduced: Hopf point in mu = nu at 0.0616 (A = 2) and 0.0314 (A = 0.7).
- Discrepancy D6: Fig. 3C, D match the mu = nu = 0.02 orbit (period 136.5; OC 0.923, PC 0.697,
  PD 0.438, OD 0.268), not the 1e-4 orbit named in the caption (period 9437).
- Discrepancy D3 resolved: A = 2 orbit passes near state 9 (PD), A = 0.7 near state 8 (OD); the
  caption's "respectively" is reversed. Mechanism: along the OC edge the strategy with the larger
  invasion threshold (y_PD = (c-B-h)/(b-f-B) vs y_OD = (c-B)/(A-B)) invades first.

## 2026-10-10 Phase 3: IBM
- src/ibm.py: count-based exact IBM (numba, about 42 ns per event).
- Small setting (Fig. 1A, B), one run of 2e5 generations: H:C = 2.16 (paper 2.15).
- Large setting (Fig. 1C, D): late means OC 0.50, PC 0.22, OD 0.05, PD 0.23, corrupt 0.53 (paper
  read-off about 0.5, 0.2, 0.05, 0.2-0.25, 0.50-0.55).
- tests/test_ibm_vs_ode.py: 7 tests pass (Fermi function, payoffs, conservation, neutral limit,
  transient and long-run agreement with the exact mean field, weak-selection limit).

## 2026-10-10 Phase 4: rare-exploration Markov chain
- src/rare_exploration.py: printed T, derived T from invasion analysis, symbolic stationary
  distribution. The derived T differs from the printed one only in rows 3 and 4 (SPEC D4, D5);
  both give exactly (7+12L)N + 33L + 54L^2 : 7 + 48L + 54L^2 (= 2.541 at N = 10, L = 1).

## 2026-10-10 Phase 5: extension
- src/rotation.py (V0-V3 continuous, pulse map), src/dde.py (method of steps), IBM rotation
  (continuous and pulse, V0-V3 with a history buffer for V3), src/metrics.py (METRICS.md).
- Tests: rho = 0 reproduces base exactly (ODE right-hand side, trajectories, and IBM trajectories
  bit for bit); V1 at kappa = 0 equals V0; V1 equals V0 at rho_eff = rho (1 - kappa) (sympy on the
  whole system, trajectories, pulse map); DDE solver matches the exact solution of y' = -y(t-1);
  IBM rotation matches its mean field (relaxation, pulses, delay).
- Key analytical finding (to be reported, R2): in the default mean-field setting (mu = nu = 0.01,
  A = 2) there is NO Hopf bifurcation in rho. The equilibrium curve is S-shaped with folds at
  rho = 0.01335 and 0.1265. The fold at 0.01335 is a saddle-node on the limit cycle (SNIC): the
  period diverges (203, 353, 988, 2546 as rho -> 0.01335) and for larger rho all starts converge
  to a stable honest equilibrium with few prudent players (x2 about 0.016). A small-mu formula
  (analysis.rho_c_approx) gives rho_c = 0.01368 (2.5% error), and rho_c is proportional to mu.
  A Hopf route appears only near the base Hopf point (mu = nu = 0.06: Hopf at rho = 0.0342).
- Test changes (not weakening): the original test assumed a Hopf in rho at mu = 0.01, which is
  false. It was replaced by (a) fold points scale as 1/(1 - kappa), (b) the Hopf point at
  mu = 0.06 scales as 1/(1 - kappa), (c) the rho_c formula matches continuation within 2%, and
  (d) a regression test that a focus-to-node change is not flagged as Hopf (a bug found here).
- Bug fixed in the IBM: records at pulse times now show the post-pulse state, matching the
  mean-field pulse map.
- Next: Phase 6 experiments (reproduction runner first, then E1-E7).

## 2026-10-10 Phase 6: experiments (full profile)
- Total full-run compute: 16.8 min for the main pipeline plus about 2 min for patched reruns
  (rep_fig3, rep_shrinkage, ext_e5, ext_e5b) on 14 worker processes. Well inside the 4 h budget;
  no reductions needed.
- B3: IBM H:C = 2.03 [2.00, 2.06] at the paper's rates (paper: 2.15; Markov: 2.54); rarer
  exploration moves it to 2.32 (mu = 3e-4) and 2.46 (mu = 1e-4), toward the Markov value.
  Doubled window: 2.03. Mismatch with 2.15 reported, not tuned (integrity rule 4).
- B4 large: late means OC 0.53, PC 0.19, OD 0.05, PD 0.23, corrupt 0.54; exact mean field
  predicts a stable focus (eigenvalues -0.0081 +- 0.0089 i): damped oscillations.
- Mean-field rotation: SNIC at rho_c = 0.0133 (formula 0.0137); period exponent -0.478.
- Hypotheses (results/full/hypotheses.json): H1 supported; H2 not supported (vigilance falls but
  remaining episodes are shallower and shorter); H3 supported (inheritance weakens rotation; the
  V1 = V0(rho_eff) equivalence fails the strict pre-registered IBM test at 2 of 15 points, holds
  with Bonferroni adjustment); H4 substitutes for honesty (mixed for cooperation); H5 mixed
  (bistability only for kappa near 1; pre-registered sweep shows no loop; post-hoc sweep from the
  corrupt state does; no start dependence in the IBM); H6 not supported (1375 points, rightmost
  root never above -3.2e-4).
- Follow-up E5b added after E5 found one bistable point; it is reported as a targeted follow-up,
  and the pre-registered verdict is kept separate.
- Bug found and fixed: IBM two-start runs in E5 used identical seeds, so chains coalesced; now
  independent seeds.
- Extra findings: pulses (whole-cohort replacement) give higher honesty than continuous rotation
  at the same average rate; newcomers with p0 <= 0.75 can lower honesty; in the large IBM,
  honesty with rotation follows (nu + rho)/(2 nu + rho) within 0.01.
- Figures 1-10 and S1-S3 generated from results only; 271 LaTeX macros in
  paper/autogen_numbers.tex.
- Next: Phase 7 documentation.
