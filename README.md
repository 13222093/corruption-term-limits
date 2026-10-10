<!-- Generated from docs_src/README.md.in by experiments/render_docs.py; edit the template, not this file. -->
# Who guards the guardians when the guardians rotate?

Umpire rotation and inherited integrity in an evolutionary model of institutional corruption.

This repository (1) reproduces the corruption model of Lee, Iwasa, Dieckmann and Sigmund,
"Social evolution leads to persistent corruption", PNAS 116:13276-13281 (2019),
doi:[10.1073/pnas.1900078116](https://doi.org/10.1073/pnas.1900078116), and (2) extends it with
term-limited umpires (rotation) whose newcomers may inherit the integrity of their predecessors.
It contains the code, all numeric results, figures, a first-draft paper in two layouts
(`paper/main.pdf`, single-column preprint; `paper/ieee/main_ieee.pdf`, IEEE two-column journal
format with IEEEtran) and notes for the author.

> **Important limitation.** The SI Appendix of Lee et al. (2019) could not be obtained (PMC shows a
> CAPTCHA, PNAS returns HTTP 403). Everything the main text delegates to the SI, in particular the
> exact individual-based update procedure, is marked UNVERIFIED in [SPEC.md](SPEC.md) and was
> resolved by documented assumptions ([DECISIONS.md](DECISIONS.md) D-003 to D-007).

## Question

In the model of Lee et al., players play a donation game supervised by umpires who are either
honest (they fine defectors) or corrupt (they take bribes). Players can pay a cost h to check
their umpire. Social learning produces cycles: honest periods let checking lapse, corruption
spreads, cooperation collapses, prudent checking returns, and honesty recovers.
We ask: what happens when umpires serve limited terms and are replaced by newcomers? Does rotation
keep institutions honest, does it remove the cycles, and what if newcomers inherit the integrity
of the body they join (linearly, by conformity, or with a delay)?

## Main results

All numbers below are generated from `results/full/` (see `results/full/numbers.md`). "Mean field"
means the deterministic large-population equations; "IBM" means the stochastic individual-based
model. The two are reported separately.

**Reproduction (Lee et al. 2019)**

| Benchmark | Paper | This repository | Status |
|---|---|---|---|
| B1: all umpires corrupt, OD -> h/(f+B) | 0.25, PC 0.75 | 0.25, 0.75 (max deviation 4.8e-12 over 20 starts) | reproduced |
| B2: all umpires honest, OC -> 1 | 1 | 1 (max deviation 2.4e-11) | reproduced |
| B3: rare-exploration H:C ratio, N = 10 | (19N+87):109 = 2.54 | 2.541, derived independently and symbolically | reproduced |
| B3: simulated H:C ratio | about 2.15 | 2.030 [2.003, 2.057] (30 runs of 200000 generations) | close, not matched |
| B4: sustained cycles (M = 50, N = 10) | about 7 episodes per 10^5 steps (read from Fig. 1) | 6.0 [6.0, 6.1] | reproduced |
| B4: damped oscillations (M = 5000, N = 1000) | corrupt fraction about 0.5-0.55 (Fig. 1D) | 0.541 [0.535, 0.545]; mean-field focus, eigenvalues -0.0081 +- 0.0089i | reproduced |
| B4: orbit shrinkage with exploration | qualitative (Fig. 3) | Hopf point at mu = nu = 0.0616 (A = 2), 0.0314 (A = 0.7) | reproduced |

The simulated ratio moves toward the Markov value as exploration becomes rarer:
2.318 at mu = 3e-4 and 2.459 at mu = 1e-4. The remaining gap to the paper's
2.15 at mu = 1e-3 is reported as a finding; the most likely cause is a difference in the
(unavailable) individual-based update details.

**Extension (new; author's design)**

1. *Rotation removes corruption cycles through a saddle-node on invariant circle (mean field).*
   At the default exploration rate (mu = nu = 0.01) there is no Hopf bifurcation in the
   rotation rate rho. A stable honest equilibrium appears in a fold at rho_c = 0.0133 that lies
   on the limit cycle; the period diverges with exponent -0.478 (theory: -1/2). A
   small-exploration formula gives rho_c = 0.0137 (2.5% error) and shows that
   rho_c is proportional to the exploration rate (rho_c / mu = 1.36 for A = 2).
2. *H1 supported.* Rotation raises time-averaged honesty and damps cycles: IBM small population
   0.669 -> 0.978 (rho = 0 -> 0.3 per generation), corruption
   episodes 3.63 -> 0.29 per 1000 generations.
3. *H2 (vigilance paradox) not supported.* Rotation does lower vigilance (prudent cooperators
   0.210 -> 0.006), but the remaining corruption episodes are shallower and
   shorter, not deeper (lowest cooperation in an episode 0.262 -> 0.643;
   duration 88.1 -> 23.3 generations).
4. *H3 supported.* Inheritance weakens rotation in all three variants. Linear inheritance is
   exactly fresh rotation at rho (1 - kappa) in the mean field. In the IBM the equivalence fails
   the strict pre-registered test at 2 of 15 points (largest
   difference 0.0073) and holds after Bonferroni adjustment.
5. *H4: substitutes.* Rotation helps honesty more when transparency is costly (gain at
   rho = 0.05: 0.134 at h = 0.02 vs 0.478 at h = 0.28). For cooperation the
   pattern is mixed.
6. *H5 mixed.* Conformist inheritance produces bistability only when newcomers almost purely
   copy the majority (kappa >= 0.95 at default parameters) and rotation is fast.
   The pre-registered hysteresis sweep shows no loop; a post-hoc sweep from the corrupt state does.
   The IBM shows no dependence on the starting state.
7. *H6 not supported.* Delayed inheritance never destabilized the honest equilibrium
   (1375 parameter points; rightmost root real part at most -3.2e-4).
8. *Robustness.* Replacing a whole cohort at once (pulses) gives more honesty than continuous
   rotation at the same average rate (IBM: 0.802 -> 0.899). Newcomers who are
   not reliably honest (p0 = 0.6) can make moderate rotation lower honesty (minimum 0.484).

Note on novelty: in the mean field, fresh-cohort rotation is algebraically the same as umpire
exploration biased toward honesty (DECISIONS.md D-015). Related ideas (enforcer "education",
higher enforcer exploration) appear in Lee et al. (2015) and Zhou et al. (2023). To our knowledge
the bifurcation structure and the inheritance variants have not been studied in this model.

## Repository layout

```
src/            model code (payoffs, ODE, DDE, IBM, Markov chain, rotation, analysis, metrics)
experiments/    run_reproduction.py, run_extension.py, run_sensitivity.py,
                evaluate_hypotheses.py, make_figures.py, make_numbers.py, render_docs.py
tests/          pytest suite (payoffs, fixed points, IBM vs ODE, Markov chain, rotation limits,
                rho_eff equivalence)
configs/        base.yaml, quick.yaml, full.yaml
results/        JSON outputs with config hash and git commit (full/ and quick/)
figures/        PNG and vector PDF (figures/quick/ for the quick profile)
paper/          main.tex, references.bib, autogen_numbers.tex, main.pdf
  ieee/         main_ieee.tex (IEEEtran journal), refs_ieee.bib (generated), main_ieee.pdf
docs_src/       templates for the Markdown documents (numbers are filled in automatically)
```

Key documents: [SPEC.md](SPEC.md) (model with source locations), [DECISIONS.md](DECISIONS.md),
[METRICS.md](METRICS.md) (pre-registered metrics and decision rules), [PROGRESS.md](PROGRESS.md),
[NOTES_for_author.md](NOTES_for_author.md), [REVIEW.md](REVIEW.md),
[FINAL_REPORT.md](FINAL_REPORT.md), [CITATIONS_TODO.md](CITATIONS_TODO.md).

## How to run

Requirements: Python 3.12 (3.11 should work), the packages in `requirements.txt` or
`environment.yml`, and a TeX distribution for the paper. Put the reference PDFs in `refs/`
(not distributed).

```bash
pip install -r requirements.txt
python -m pytest
make all                     # on Windows: mingw32-make all
python run_all.py full       # same pipeline without make
make quick                   # fast check with the quick profile
```

Recorded compute: about 17 minutes for the full profile and 2 minutes for
the quick profile on a 16-thread laptop (14 worker processes).
Individual steps: `python experiments/run_reproduction.py full`,
`python experiments/run_extension.py full [bif e1 e2 e3 e4 e5 e5b e6]`,
`python experiments/run_sensitivity.py full`, `python experiments/evaluate_hypotheses.py full`,
`python experiments/make_figures.py full`, `python experiments/make_numbers.py full`,
`python experiments/render_docs.py`, `python experiments/build_paper.py`.

## Reproduction notes: discrepancies and resolved typos

| ID | Where | Issue | Resolution |
|---|---|---|---|
| D1 | Methods p.13281 | Q(y) printed as y1 Q_C + (1 - y1) Q_H although y1 is the honest fraction (also in the PDF, not only PMC) | Q(y) = y1 Q_H + (1 - y1) Q_C; the printed form fails B1 (test) |
| D2 | Methods p.13281 | Honest mixed state called "OD+PD (a mixture of OD and PC)" | It is OD and PD (Fig. 2 caption, Q_H) |
| D3 | Fig. 3 caption | "8 or 9, respectively" is reversed relative to the figure | With A = 2 the orbit passes state 9 (distance 0.142), with A = 0.7 state 8 (distance 0.022); explained by the invasion thresholds y_PD = 0.333, y_OD = 0.167 (A = 2) or 0.600 (A = 0.7) |
| D4 | Transition matrix T | Row 3 omits allOD (H) -> allOD (C) | State 3 is transient; stationary distribution unchanged (symbolic check) |
| D5 | Transition matrix T | Row 4 entry mu/6 for a neutral player mutant, while other neutral player mutants get 0 | Transient row; no effect |
| D6 | Fig. 3C, D | Caption says the orange orbit (mu = nu = 1e-4) is shown; its period is 9437 time units | The panels match the mu = nu = 0.02 orbit (period 136.5; peaks OC 0.923, PC 0.697, PD 0.438, OD 0.268) |
| U1-U4 | SI Appendix | Not available | IBM update scheme, payoff evaluation and time unit resolved by assumptions; see SPEC.md Section 8 |
| PMC | Web version | Minus signs lost | All signs read from the PDF at 300 dpi and checked symbolically |

## Citation

If you use this code, cite the original model:

Lee J-H, Iwasa Y, Dieckmann U, Sigmund K (2019). Social evolution leads to persistent corruption.
*Proceedings of the National Academy of Sciences* 116(27):13276-13281. doi:10.1073/pnas.1900078116

and this repository: Aziz, M. A. A. (2026). Umpire rotation and inherited integrity in an
evolutionary model of institutional corruption (code and preprint draft). [repository URL]

## License

MIT (see [LICENSE](LICENSE)). The reference PDFs in `refs/` are not part of the repository.
