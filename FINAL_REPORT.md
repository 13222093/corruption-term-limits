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
| B3 simulated ratio | about 2.15 | time all honest / all corrupt 2.134 [2.102, 2.165]; ratio of mean shares 2.030 [2.003, 2.057]; rarer exploration (mean shares): 2.318, 2.459 | matched under the Markov-type definition; the SI does not state the definition |
| B4 sustained cycles | about 7 episodes per 1e5 steps (read off) | 6.0 [6.0, 6.1] | consistent |
| B4 damped oscillations | corrupt about 0.50-0.55 (read off) | 0.541 [0.535, 0.545]; stable focus -0.0081 +- 0.0089i | consistent |
| B4 orbit shrinkage | qualitative | Hopf at mu = nu = 0.0616 (A = 2), 0.0314 (A = 0.7) | reproduced |
| Fig. 3C, D values | read off: OC 0.93, PC 0.70, PD 0.45, OD 0.27, period about 137 | at mu = nu = 0.02: 0.923, 0.697, 0.438, 0.268, period 136.5 | match (see D6) |

The fallback project (Section 14 of CLAUDE.md) was not needed: B1 and B2 passed.

## 2. Notation inconsistencies and other reproduction notes
The reproduction relies on the clear and detailed description by Lee et al. (2019). In a few
places the text can be read in more than one way; none of these affects their conclusions.
- **D1** The printed Methods weight Q(y) as y Q_C + (1 - y) Q_H, while y is the honest fraction.
  We read it as y Q_H + (1 - y) Q_C, which gives the stated B1 and B2; read literally, the
  all-corrupt case ends at OC = 1.000.
- **D2** The honest mixed state is labelled "OD+PD (a mixture of OD and PC)"; we read it as a
  mixture of OD and PD.
- **D3** The Fig. 3 caption lists "8 or 9, respectively" in the opposite order to the panels;
  we follow the panels, as the SI does. This is explained by the
  invasion thresholds y_PD = 0.333 and y_OD = 0.167 (A = 2) or 0.600 (A = 0.7).
- **D4** The printed T has no entry for allOD(H) -> allOD(C), while the SI text (p.2) describes
  corrupt umpires invading this state. The row is transient, so the stationary distribution is
  the same either way. Our derivation uses the SI's fixation rules and reproduces the printed T
  in every other entry.
- **D6** Fig. 3C, D are labeled as the mu = nu = 1e-4 orbit (period 9437), but match the
  mu = nu = 0.02 orbit.
- **D7 (from the SI)** In SI Fig. 9 the axis labels of the panels are exchanged relative to
  the caption; we follow the caption.
- **B3 definition** The published 2.15 is matched by the time with all umpires honest over the
  time with all umpires corrupt (2.134), not by the ratio of mean shares
  (2.030; 2.037 in runs of 2.2e8 steps). Burn-in, starting state,
  imitation strength, exploration and payoff conventions do not explain the difference
  (CHANGES_SI.md Section 5). The SI does not state the definition (U3).
- **PMC** The web version does not display the minus signs of the payoff matrices; all signs
  were taken from the PDF.
- **SI** read in full (SI_EXTRACT.md). It states the exploration rules, the fixation rules behind
  T and the cost-free chain; all match our model. It does not give the individual-based update
  order, role-model sampling, finite-population payoffs or the averaging behind 2.15; these
  remain documented assumptions. SI Fig. 8 cycle counts support our time unit: s = 10 panels
  within 6%, s = 1 panels 0% to 38% higher
  in our model (single SI runs).

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
IBM update order and role-model sampling are assumptions (the SI does not state them, although
every rule it states holds and its Fig. 8 supports the time unit); the definition of the time
average behind the published 2.15 is not stated; qualitative cross-level comparison (different time units and
imitation rules); well-mixed populations; equal learning rates; simple inheritance rules;
two-player games; global attraction above rho_c shown numerically, not proved; H5 region found by
a follow-up. See REVIEW.md.

## 7. Open items for the author
1. The SI was obtained and checked (SI_EXTRACT.md, CHANGES_SI.md). Remaining: ask the authors
   which time average gave 2.15 and which update order their simulation used (U1, U3).
2. Push the repository (PUSH_INSTRUCTIONS.md; GitHub CLI was not available, so nothing has been
   pushed), then fill in the repository URL in README, CITATION.cff, CV_ENTRY and both papers,
   and the email, ORCID and further acknowledgements in both papers.
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
python experiments/digitize_si.py full      # needs refs/pnas.1900078116.sapp.pdf
python experiments/run_reproduction.py full
python experiments/run_extension.py full
python experiments/run_sensitivity.py full
python experiments/evaluate_hypotheses.py full
python experiments/make_figures.py full
python experiments/make_numbers.py full
python experiments/make_changes_si.py
python experiments/render_docs.py
python experiments/build_paper.py
```
Recorded compute: about 17 minutes (full) and 3 minutes (quick).

## 9. Definition of done (CLAUDE.md Section 15)
- [x] All tests pass (100); `make all` regenerates everything (quick pipeline, numbers, docs and
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

## 10. SI verification (branch si-verification)
- SI obtained from an Internet Archive copy of the PNAS supplementary file (SI_EXTRACT.md
  Section 1; 10 pages, SHA-256 recorded there).
- `ibm_variant: si` is the default; `ibm_variant: reconstructed` is kept selectable. Because the
  SI does not specify the update procedure, both run the same kernel (identical results:
  yes).
- Markov derivation updated to the SI fixation rules; the SI's cost-free chain and closed form
  reproduced exactly (tests in `tests/test_rare_exploration.py`, `tests/test_si_rules.py`).
- Full pipeline rerun: no simulated value and no hypothesis outcome changed; two diagnostics of
  the derived Markov chain changed as expected
  (CHANGES_SI.md Section 3).
