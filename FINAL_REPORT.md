<!-- Generated from docs_src/FINAL_REPORT.md.in by experiments/render_docs.py; edit the template, not this file. -->
# FINAL_REPORT.md

Project: *Who guards the guardians when the guardians rotate?* Reproduction of Lee, Iwasa,
Dieckmann and Sigmund (PNAS 2019) and an extension with umpire rotation and inherited integrity.
All numbers below are generated from `results/full/`.

## 1. What was reproduced, and how closely

| Benchmark | Published | Obtained | Verdict |
|---|---|---|---|
| B1 all corrupt | OD 0.25, PC 0.75 | OD 0.25, PC 0.75; max deviation 4.8e-12 (20 random starts) | exact |
| B2 all honest | OC -> 1 | OC -> 1; max deviation 2.4e-11 | exact |
| B3 Markov ratio (N = 10) | (19N+87):109 = 2.54 | 2.541; same closed form from an independent derivation of T | exact |
| B3 simulated ratio | about 2.15 | 2.030 [2.003, 2.057]; rarer exploration: 2.318, 2.459 | close; lower than published; CI excludes 2.15 |
| B4 sustained cycles | about 7 episodes per 1e5 steps (read off) | 6.0 [6.0, 6.1] | consistent |
| B4 damped oscillations | corrupt about 0.50-0.55 (read off) | 0.541 [0.535, 0.545]; stable focus -0.0081 +- 0.0089i | consistent |
| B4 orbit shrinkage | qualitative | Hopf at mu = nu = 0.0616 (A = 2), 0.0314 (A = 0.7) | reproduced |
| Fig. 3C, D values | read off: OC 0.93, PC 0.70, PD 0.45, OD 0.27, period about 137 | at mu = nu = 0.02: 0.923, 0.697, 0.438, 0.268, period 136.5 | match (see D6) |

The fallback project (Section 14 of CLAUDE.md) was not needed: B1 and B2 passed.

## 2. Every discrepancy found
- **D1** Q(y) weighting swapped in the printed Methods (in the PDF itself). Resolved to
  y Q_H + (1 - y) Q_C; the printed form fails B1 (OC -> 1.000 with all umpires corrupt).
- **D2** Honest mixed state misnamed "OD+PD (a mixture of OD and PC)"; it is OD and PD.
- **D3** Fig. 3 caption "8 or 9, respectively" reversed relative to the figure; explained by the
  invasion thresholds y_PD = 0.333 and y_OD = 0.167 (A = 2) or 0.600 (A = 0.7).
- **D4** Printed T omits allOD(H) -> allOD(C); transient row, no effect.
- **D5** Printed T gives mu/6 to a neutral player mutant in row 4; transient row, no effect.
- **D6** Fig. 3C, D are labeled as the mu = nu = 1e-4 orbit (period 9437), but match the
  mu = nu = 0.02 orbit.
- **B3 gap** Simulated ratio 2.030 vs published 2.15; most likely due to the
  reconstructed update procedure (SI unavailable).
- **PMC** web version lost minus signs; all signs taken from the PDF.
- **SI** not available (U1-U4 in SPEC.md): IBM update scheme, payoff evaluation, time unit, and
  T derivation were reconstructed or re-derived.

## 3. Hypothesis outcomes (pre-registered rules in METRICS.md)
| Hypothesis | Outcome | Mean field | Finite population |
|---|---|---|---|
| H1 rotation raises honesty, damps cycles | supported | cycles vanish at rho_c = 0.0133 (SNIC); honesty 0.581 -> 0.957 at rho = 0.2 | honesty 0.669 -> 0.978; episodes 3.63 -> 0.29 per 1000 generations |
| H2 vigilance paradox | not supported | PC 0.174 -> 0.036; peak corruption 0.980 -> 0.955 | PC 0.210 -> 0.006; lowest cooperation in episodes 0.262 -> 0.643; duration 88.1 -> 23.3 |
| H3 inheritance weakens rotation | supported | V1 = V0 at rho (1 - kappa), exact; V2, V3 also weaker | honesty falls with kappa for V1, V2, V3; V1 vs V0(rho_eff): 2 of 15 CIs exclude 0 (holds after Bonferroni) |
| H4 rotation vs transparency | substitutes (mean field and IBM agree) | gain rises with h in 273/300 pairs (honesty); mixed for cooperation | 29/32 pairs |
| H5 conformist bistability | mixed | 1/240 bistable in the pre-registered scan; open region only for kappa >= 0.95; no loop in pre-registered sweep, loop post hoc | no dependence on the starting state |
| H6 delay destabilizes | not supported | rightmost root <= -3.2e-4 over 1375 points | not tested separately (mean-field question) |

## 4. Key figures
- `figures/fig04_bifurcation_rho.pdf`: SNIC in rho, period scaling (slope -0.478),
  two-parameter diagram.
- `figures/fig07_vigilance_h2.pdf`: vigilance falls, episodes get shallower (H2).
- `figures/fig06_rho_kappa.pdf`: inheritance weakens rotation (H3).
- `figures/fig01..03`: reproduction. Full list in `figures/README.md`.

## 5. Additional findings
- Small-exploration formula for the critical rotation rate: 0.0137 vs exact 0.0133;
  rho_c / mu = 1.36 (A = 2) and 3.35 (A = 0.7).
- rho_c depends non-monotonically on h (peak 0.0165 near h = 0.04, 0.0017 at
  h = 0.28) because the PD invasion threshold falls with h.
- Whole-cohort pulses beat continuous rotation at the same mean rate (mean field
  0.737 -> 0.825; IBM 0.802 -> 0.899).
- Newcomers who are not reliably honest raise rho_c (0.0174, 0.0302,
  0.0739 for p0 = 0.9, 0.75, 0.6), and with p0 = 0.6 rotation can lower honesty
  (to 0.484).
- Large populations: honesty with rotation is within 0.008 of (nu + rho)/(2 nu + rho).

## 6. Limitations
Reconstructed IBM (SI unavailable); qualitative cross-level comparison (different time units and
imitation rules); well-mixed populations; equal learning rates; simple inheritance rules;
two-player games; global attraction above rho_c shown numerically, not proved; H5 region found by
a follow-up. See REVIEW.md.

## 7. Open items for the author
1. Download the SI Appendix (pnas.1900078116.sapp.pdf) manually, put it in refs/, and check
   SPEC.md items U1-U4; if the update rule differs, rerun `make all`.
2. Fill in the repository URL, email, ORCID and acknowledgements in paper/main.tex and README.
3. Decide whether to keep A = 0.7 and the two-parameter Hopf region in the main text.
4. Consider a formal derivation of rho_c (matched asymptotics) and an analysis of pulses as a
   periodically forced system.
5. Read NOTES_for_author.md before interviews; the answers there are honest about the gaps.

## 8. Exact commands to regenerate everything
```bash
pip install -r requirements.txt
python -m pytest
mingw32-make all            # or: make all (Linux/macOS), or: python run_all.py full
```
Equivalent step by step:
```bash
python experiments/run_reproduction.py full
python experiments/run_extension.py full
python experiments/run_sensitivity.py full
python experiments/evaluate_hypotheses.py full
python experiments/make_figures.py full
python experiments/make_numbers.py full
python experiments/render_docs.py
python experiments/build_paper.py
```
Recorded compute: about 17 minutes (full) and 2 minutes (quick).

## 9. Definition of done (CLAUDE.md Section 15)
- [x] All tests pass (80); `make all` regenerates everything (quick pipeline, numbers, docs and
      paper verified from a clean clone; the full profile was run in the working copy).
- [x] SPEC.md, DECISIONS.md, METRICS.md, PROGRESS.md complete.
- [x] B1 to B4 attempted and reported with numbers.
- [x] H1 to H6 each marked supported, not supported or mixed.
- [x] All figures generated with full captions (paper/main.tex).
- [x] README, NOTES_for_author.md, SOP_sentences.md complete.
- [x] paper/main.pdf compiled; numbers via macros only. IEEE two-column version:
      paper/ieee/main_ieee.pdf (same content, same macros, IEEEtran journal format).
- [x] REVIEW.md and CITATIONS_TODO.md complete.
- [x] FINAL_REPORT.md (this file).
