# PROGRESS.md

Log of completed tasks: what was done, results, next step. Newest entries at the bottom.

## 2026-10-10 Phase 0: setup and specification
- Read the project brief and all four PDFs in refs/. The PNAS paper is a scanned image PDF; read visually
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

## 2026-10-10 Phases 7-8: documentation and paper
- Markdown documents are rendered from templates in docs_src/ by experiments/render_docs.py, so
  every number comes from paper/autogen_numbers.tex (generated from results/full/).
- README.md (question, results, how to run, reproduction notes, citation, license),
  the author notes (concepts, how to read each figure, 10 interview questions),
  the SOP sentences (3 sentences, 204-271 characters).
- paper/main.tex compiled with MiKTeX to paper/main.pdf (21 pages; main text about 6000 words of
  prose plus captions; 26 verified references; no undefined references or overfull boxes).
- Makefile (mingw32-make on Windows), run_all.py, experiments/build_paper.py.
- Next: Phase 9 self-review, clean-clone test, FINAL_REPORT.md.

## 2026-10-10 Phase 9: self-review and final report
- REVIEW.md written as a critical referee (7 major, 8 minor points; checklist all satisfied).
  Fixes applied to the paper: "small populations" in the abstract, "three initial states",
  H2 mechanism marked untested, counts via macros, table widths, float barriers.
- Clean-clone test: `mingw32-make quick` (80 tests + quick pipeline) ran in 3 min without
  errors; `mingw32-make numbers docs paper` regenerated identical content (only line endings and
  PDF timestamp differ).
- FINAL_REPORT.md written. Project complete; open items for the author listed there.

## 2026-10-10 IEEE version of the paper (user request)
- paper/ieee/main_ieee.tex: IEEEtran two-column journal format (Index Terms, IEEE section
  numbering, table captions above tables, figure* for multi-panel figures, appendices before the
  acknowledgment, IEEEtran.bst references). Same text, figures and number macros as
  paper/main.tex.
- IEEEtran.bst ignores the doi field, so experiments/build_paper.py generates
  paper/ieee/refs_ieee.bib from paper/references.bib with each DOI added as a "doi:" note.
- Compiled to paper/ieee/main_ieee.pdf: 13 pages, no errors, no overfull boxes, no undefined
  references; all 26 references show their DOI. `make paper` now builds both versions.

## 2026-10-10 SI verification (branch si-verification)
- Snapshot of all pre-SI full results in results/pre_si/ (commit aef9a3f).
- Step 1: SI obtained from an Internet Archive copy of the PNAS supplementary file (PNAS 403,
  PMC CAPTCHA not bypassed, Europe PMC not open access). SI_EXTRACT.md lists every SI statement
  on U1-U4 and D1-D6 with page references (D-016, D-020).
- Step 2: `ibm_variant: si` (default) and `ibm_variant: reconstructed` added. The SI does not
  specify the update procedure, so both run the same kernel (D-017). The Markov derivation now
  applies the SI fixation rules for neutral mutants; the derived T equals the printed T except D4,
  D5 is withdrawn, the h = 0 chain is supported (D-018, D-019). New tests: tests/test_si_rules.py
  (17) and SI checks in tests/test_rare_exploration.py; 100 tests pass.
- Step 3: both variants rerun side by side (identical). B3 gap investigated one cause at a time
  (rep_b3_diag): the gap closes only under the all-honest / all-corrupt time definition; burn-in,
  starting state, imitation strength, run length and update conventions do not explain it
  (D-022). New checks against SI Fig. 8 (cycle counts, digitized by script, D-021), SI Fig. 9B
  (periods) and the h = 0 chain. Fig. S4 added.
- Step 4: full pipeline rerun (`python run_all.py full`, log logs/full_run_si.log).
- Step 5: CHANGES_SI.md written (template docs_src/CHANGES_SI.md.in; old/new table generated by
  experiments/make_changes_si.py). README, FINAL_REPORT, REVIEW, author notes, SOP sentences,
  paper/main.tex and paper/ieee/main_ieee.tex updated.
- Step 4 result: full pipeline finished in 18 min, 100 tests passed. Every result file equals the
  pre-SI snapshot except runtimes and rep_markov.json (derived-vs-printed differences 4 -> 2;
  finite-M chain ratio 2.540 -> 2.541, now equal to the closed form 277/109).
- Step 5 result: CHANGES_SI.md generated (78 finite-population quantities compared, 2 changed,
  both Markov diagnostics; 0 of 6 hypothesis outcomes flipped). Both papers compile without
  undefined references or overfull boxes (main.pdf 23 pages, main_ieee.pdf 14 pages); no em dashes
  or unresolved macros in any rendered document; SOP sentences 204-281 characters.

### Final summary of the SI verification
- The SI does not specify the individual-based update procedure. Every rule it states holds in
  our model, and its Fig. 8 cycle counts support our time unit. The SI-faithful model is
  therefore the reconstruction; both `ibm_variant` values run the same kernel.
- The Markov derivation was corrected to the SI fixation rules: D5 withdrawn, D4 confirmed, SI
  cost-free chain reproduced exactly. D7 (SI Fig. 9 axis labels) added.
- B3: the published 2.15 is matched by the time with all umpires honest over the time with all
  umpires corrupt (2.134 [2.102, 2.165]), not by the ratio of mean shares (2.030). No other
  candidate cause explains the gap. The SI does not state the definition, so this stays open (U3).
- No simulated result and no hypothesis outcome changed.

## 2026-10-10 Release task
- Part 1: tests passed on si-verification (100); `master` renamed to `main`; si-verification
  merged with --no-ff; tests passed on main (100). refs/ confirmed never committed. logs/,
  results/quick/, figures/quick/ and the duplicated pre-SI JSON files removed from the tree
  (D-023). digitize_si.py falls back to the committed read-offs when refs/ is absent. README top
  section, key figure, run guide and "Tools and assistance" note; CITATION.cff added.
- Part 2: paper/main.tex and paper/ieee/main_ieee.tex define both B3 time averages in Methods,
  report both in Results (2.030 mean shares; 2.134 all honest / all corrupt, which contains 2.15),
  and add Table 3 / Table IV in the reproduction appendix with the majority variant and all other
  B3 checks (macros only). README wording aligned. Both PDFs compile without undefined references.
- Part 3: neutral wording applied to both papers, README, FINAL_REPORT, REVIEW, NOTES (new Part 4
  "How to talk about discrepancies"), SOP (sentence 1 now states a verified result instead of a
  count of inconsistencies; 293 characters), CHANGES_SI, SPEC, SI_EXTRACT and three code comments
  (80 replacements, WORDING_AUDIT.md). D5 removed outside the change logs. Paper main text has one
  sentence on notation inconsistencies; Appendix B has a neutral table of D1-D4, D6, D7.
  Acknowledgements credit Lee et al. and disclose AI assistance. A CV entry was added (template,
  numbers from results). Tests pass (100); both papers compile without undefined references or
  overfull boxes.
- Release: PUSH_INSTRUCTIONS.md written (no git remote and no GitHub CLI on this computer, so
  nothing was pushed). Annotated tag v1.0.0 created on main.

### Final summary of the release task
- What changed: si-verification merged into main (renamed from master); regenerable outputs and
  build logs removed from the tree; README rewritten for readers arriving from a CV (summary,
  key figure, citation, run guide, tools and assistance); CITATION.cff; B3 reported under both
  time-average definitions in both papers with an appendix table; neutral wording throughout
  (WORDING_AUDIT.md); the CV entry. No result changed: results/full/ is untouched apart from the
  SI read-off fallback, which reuses the committed file.
- Checks: 100 tests pass on main; both papers compile without undefined references, undefined
  macros or overfull boxes; no em dashes; refs/ never committed; no secrets, emails or local
  paths in the current tree (old build logs with a local path remain in earlier commits,
  D-023).
- Repository URL: not pushed. Follow PUSH_INSTRUCTIONS.md, then replace the placeholder URL in
  the CV entry, README, CITATION.cff and both papers.
- Open items for the author: push and fill in the URL, email and ORCID; decide whether the
  SOP sentences, the author notes, the CV entry and the project brief should be public (done:
  kept private, D-026); ask Lee et al. which time average gave 2.15 and which update order they
  used.
