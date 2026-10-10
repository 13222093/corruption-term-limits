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
