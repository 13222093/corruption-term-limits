# PLAN.md

Project: Who guards the guardians when the guardians rotate?
Reproduction of Lee, Iwasa, Dieckmann and Sigmund (2019, PNAS 116:13276) and an
extension with umpire rotation and inherited integrity.

## Phases and tasks

| Phase | Tasks | Output |
|---|---|---|
| 0 | Repo layout, environment, Makefile, read refs/, SPEC.md, DECISIONS.md | SPEC.md, DECISIONS.md, PLAN.md, PROGRESS.md |
| 1 | Payoff matrices Q_H, Q_C, umpire income, inequalities; tests by brute-force pair enumeration | src/params.py, src/payoffs.py, tests/test_payoffs.py |
| 2 | Replicator-mutator ODE, fixed points, Jacobian, stability; B1, B2; orbit shrinkage (Fig. 3) | src/replicator_mutator.py, src/analysis.py, tests/test_fixed_points.py |
| 3 | Individual-based model (numba), its exact mean field (Fermi imitation ODE), validation at large M, N; B4 | src/ibm.py, tests/test_ibm_vs_ode.py |
| 4 | Rare-exploration Markov chain: derive T from payoffs, compare with printed T, B3 vs long simulations | src/rare_exploration.py |
| 5 | Rotation V0-V3 in ODE, DDE and IBM (continuous and pulse) | src/rotation.py, src/dde.py, tests/test_rotation_limits.py, tests/test_rho_eff_equivalence.py |
| 6 | METRICS.md (committed before experiments), mean-field analysis (Hopf in rho), E1-E7 | results/, figures/ |
| 7 | README, NOTES_for_author.md, SOP_sentences.md | docs |
| 8 | LaTeX paper with autogen numbers | paper/ |
| 9 | REVIEW.md, fixes, FINAL_REPORT.md | |

## Order of work inside each phase
1. Write tests first where a property is known (signs, limits, equivalences).
2. Implement, run quick config, then full config.
3. Write numeric outputs to results/ with config hash and git commit.
4. Update PROGRESS.md, commit.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| SI Appendix not available (PMC CAPTCHA, PNAS 403) | Use main text as source; mark IBM details as ASSUMPTION; derive Markov chain independently from payoffs |
| Q(y) weighting typo in the PDF | Resolve from Fig. 2 and limits (B1, B2); test both readings |
| IBM time unit unknown | Infer from Fig. 1 time axes and caption; document; report time in both steps and generations |
| s = 1e10 overflow in Fermi function | Numerically stable logistic; ties give exactly 1/2 |
| Near-heteroclinic orbits at small mu are stiff | LSODA/Radau with rtol 1e-9; 10x tolerance check |
| DDE solver correctness | Method of steps on solve_ivp dense output; test against exact solution of y' = -y(t-1) |
| Compute budget (4 h) | numba IBM, joblib over 16 cores, quick configs first, document any reduction |
| No LaTeX | Install MiKTeX via winget; fallback main.tex plus Markdown |
| No GNU make | Use mingw32-make (available); document; also provide `python run_all.py` |

## Compute plan (full config, rough)
- ODE sweeps: about 10^4 integrations of length 10^4: about 30 min on 16 cores.
- IBM: 30 replicates x about 60 conditions x 2x10^7 events: about 40 min on 16 cores.
- B3 long runs: 30 x 10^8 events: about 15 min.
