# DECISIONS.md

Each entry: what was decided, why, alternatives considered. Entries are append-only; later
changes are new entries that reference the old one.

## D-001 Q(y) weighting (resolves SPEC D1)
- What: Q(y) = y1 Q_H + (1 - y1) Q_C, with y1 the honest fraction.
- Why: the PDF (Methods p.13281) prints y1 Q_C + (1 - y1) Q_H, but Fig. 2 caption places the
  honest simplex at y1 = 1, dy1/dt uses P_H - P_C, and the text (p.13278) states B1/B2 for all
  corrupt/all honest. Only the swapped weighting satisfies B1 and B2. A test shows the printed
  weighting fails B1.
- Alternatives: keep printed formula and reinterpret y1 as corrupt fraction. Rejected: it would
  also require flipping the sign of the dy1/dt selection term, contradicting the printed P_H - P_C.

## D-002 Software environment
- What: Python 3.12.8 (system install), pip packages numpy 2.2.6, scipy 1.13.1, sympy 1.14.0,
  matplotlib 3.9.2, pandas 2.2.3, numba 0.68.0, joblib, pyyaml, pytest. environment.yml is
  provided for conda users and pins python 3.12.
- Why: the project brief asks for 3.11; 3.12 is what is installed, conda is not installed, and nothing in
  the code depends on the 3.11/3.12 difference.
- Alternatives: install Python 3.11 side by side. Rejected as unnecessary risk to the user's system.

## D-003 IBM time unit and update scheme (SPEC A1, UNVERIFIED U1)
- What: asynchronous random sequential updating. One elementary step = one individual chosen
  uniformly from all M + N individuals updates. Time reported in steps (to compare with Fig. 1)
  and in generations (1 generation = M + N steps).
- Why: (a) caption of Fig. 1 says new strategies enter both populations at the same rate when
  M mu = N nu, which holds if each individual updates at the same per-capita rate; (b) the Markov
  chain predicts a mean cycle of order 10^2 generations at M mu = N nu = 0.05, which matches the
  about 7 episodes per 10^5 steps in Fig. 1A only if a time unit is one elementary step.
- Alternatives: (i) one player and one umpire per step (would make the per-step entry rates
  0.001 and 0.005, i.e. lambda = 5, contradicting the caption); (ii) synchronous generations
  (would put about 300 cycles in the Fig. 1A window instead of about 7).

## D-004 Role model sampling (SPEC A2)
- What: role model drawn uniformly from the other individuals of the focal's population.
- Why: standard pairwise-comparison process; the paper says "randomly chosen role model".
- Alternatives: allow self as role model (only rescales time by (M-1)/M).

## D-005 Finite-population payoffs (SPEC A3)
- What: expected payoffs from current counts. Player co-player drawn from the other M - 1 players;
  umpire honest with probability N1/N. Umpire payoff averaged over pairs of distinct players.
- Why: the paper says payoffs depend "in an obvious way" on M1..M4, N1, N2. Excluding self is the
  usual finite-population convention. It reduces to the paper's formulas as M -> infinity.
- Alternatives: sampled games (noisy payoffs). Rejected: the paper speaks of average payoffs.

## D-006 Exploration (SPEC A4)
- What: an exploring individual switches to one of the other strategies uniformly at random.
- Why: matches the mutation term of the ODE and the mu/3 entries of T.

## D-007 Fermi function at s = 1e10
- What: evaluate 1/(1 + exp(s d)) with a numerically stable branch; exact ties give 1/2.
- Why: s d overflows for |d| > 7e-8. Payoff ties that are exact in theory (e.g. P_H = P_C = 2f at
  allOC) are exact in floating point because the formulas reduce to the same operations; a test
  checks this.

## D-008 Build tool
- What: Makefile with plain `python ...` recipes; on this Windows machine run with `mingw32-make`.
  A `run_all.py` script runs the same pipeline without make.
- Why: GNU make is not installed; mingw32-make is.

## D-009 SI Appendix unavailable
- What: proceed from the main text; mark SI-dependent items UNVERIFIED (SPEC Section 0).
- Why: integrity rule 1 of the project brief. Access attempts: PMC (CAPTCHA, not bypassed), PNAS (HTTP 403),
  IIASA PURE (bot protection).

## D-010 Default delay in V3
- What: continuous rotation: T_lag = 1/rho (mean term length). Pulse rotation: T_lag = T.
  E6 varies T_lag independently.
- Why: the project brief says "T_lag = one term"; under continuous rotation the mean term is 1/rho.

## D-011 Rotation in the IBM
- What: rotation is an extra event type. Per generation, the expected number of events is M player
  updates, N umpire updates and rho N umpire replacements. Each event advances time by
  1/(M + N + rho N) generations. A replaced umpire is chosen uniformly; the newcomer is honest with
  probability p_new computed from the honest fraction just before the replacement.
- Why: gives the exact mean field dy/dt = [base] + rho (p_new - y), matching the ODE term.
- Alternatives: replace inside an umpire update with probability rho (would rescale the base
  update rate by 1 - rho).

## D-012 Validation target for the IBM
- What: the IBM is validated against its own exact large-population limit, the "Fermi imitation
  ODE": dx_i/dt = (1 - mu) x_i sum_j x_j tanh(s (P_i - P_j)/2) + mu ((1 - x_i)/3 - x_i), and the
  analogous equation for y. For small s this is the replicator-mutator equation with time scaled
  by s/2 and exploration rates scaled by 2/s.
- Why: the paper's replicator-mutator ODE is the weak-selection limit of the Fermi process, not
  its exact limit at s = 0.3. Comparing the IBM with the wrong ODE would confound model error with
  finite-size effects.

## D-013 Mean-field exploration rates for the extension
- What: mu = nu = 0.01 as the default for mean-field extension experiments; robustness at
  mu = nu = 0.001 and 0.02 (E7).
- Why: base cycle periods are about 9400 (1e-4), 1109 (1e-3), 204 (0.01), 136.5 (0.02) time units,
  and the Hopf point is at mu = nu = 0.0616. At 0.01 the base dynamics cycle with deep corruption
  (min y about 0.02), and the period is short enough that a 10^4 window holds about 50 cycles.
- Alternatives: 1e-4 (the orange orbit of Fig. 3) has a period near 10^4 and nearly heteroclinic
  behavior, which makes heatmaps costly and sensitive to integration windows. 0.02 is the orbit
  that Fig. 3C, D actually show (SPEC D6) and is used as a robustness case.

## D-014 Discrepancy D6 (Fig. 3C, D)
- What: the caption says Fig. 3C, D show the orange (mu = nu = 1e-4) limit cycle. Our integration
  gives period 9437 at 1e-4 but 136.5 at 0.02, with peak frequencies (OC 0.923, PC 0.697, PD 0.438,
  OD 0.268, min honest 0.047) that match the Fig. 3C, D read-offs. We report Fig. 3C, D as
  matching the violet orbit (mu = nu = 0.02) and treat the caption as a labeling error.
- Alternatives: different time scaling of the ODE. Rejected: no single time factor maps the 1e-4
  orbit amplitudes onto the figure.

## D-015 Relation of V0 rotation to biased exploration (honest reporting)
- What: in the mean field, V0 rotation with p0 = 1 adds rho (1 - y) to dy/dt. Together with the
  exploration term nu (1 - 2y) this is (nu + rho)(1 - y) - nu y: umpire exploration that is biased
  toward honesty. The paper and README state this equivalence explicitly. Rotation differs from
  biased exploration in the IBM only through who is replaced (any umpire, at a fixed rate,
  independent of the imitation step), and in the extension variants (inheritance V1-V3, pulses).
- Why: Lee, Sigmund, Dieckmann, Iwasa (2015, illegal logging) studied enforcer "education" that
  raises the trial rate of honest conduct; Zhou et al. (2023) found higher enforcer exploration
  rates reduce corruption. Our V0 result is close in spirit; novelty is claimed only for
  (a) the bifurcation structure (SNIC at a critical rate rho_c proportional to the exploration
  rate, with a small-mu formula) in the Lee et al. (2019) model, and (b) the inheritance variants.
- Alternatives: claim rotation as entirely new. Rejected: not supported by the search.

## D-016 Literature search (project brief, Section 13)
- What: web searches (2026-10-10) for evolutionary-game models of corruption with rotation, term
  limits or turnover of enforcers. Found none that model rotation of enforcers in an
  evolutionary game. Related: Lee et al. 2015 (JTB, enforcer education), Liu, Chen and Szolnoki
  2019 (M3AS, corrupt enforcers), Shi et al. 2023 and Zhou et al. 2023 (AMC, supervision of
  umpires), Abbink 2004 (experimental staff rotation), Ferraz and Finan 2011 (empirical term
  limits). The paper says "to our knowledge" and lists these.

## D-017 SI verification: the SI does not specify the individual-based procedure
- What: the SI (refs/pnas.1900078116.sapp.pdf, obtained 2026-10-10 from the Internet Archive copy
  of the publisher's file; see SI_EXTRACT.md) contains no update order, time unit, finite-
  population payoff rule or averaging procedure. Every rule it does state (exploration targets,
  nu = mu M / N, ties at 1/2, the single-dissident argument implying self-excluded payoffs,
  neutral umpire fixation 1/N) is already satisfied by the reconstruction. The "SI-faithful"
  default (`ibm_variant: si`) therefore runs the same kernel as `ibm_variant: reconstructed`;
  both give identical output for the same seed (test). The switch is kept so that a future
  difference can be compared without code changes.
- Why: integrity rules forbid inventing a procedure the SI does not state; changing the model
  without SI support would be tuning.
- Alternatives: (i) adopt a different plausible scheme as "si" (rejected: no SI basis);
  (ii) remove the switch (rejected: the task asks for a selectable comparison).

## D-018 Replaced test on the derived transition matrix
- What: `test_derived_T_matches_printed_except_documented_entries` expected the derived T to
  differ from the printed T at (4,2) because neutral player mutants were ignored. The SI (p.2)
  states the rule that produces mu/6 there (a neutral dissident that gains an advantage once there
  are two copies fixes with probability 1/2). The test was replaced by
  `test_derived_T_matches_printed_except_D4` plus tests of the SI rule and of the SI's h = 0
  chain. The replaced test encoded our reconstruction, which the SI contradicts.

## D-019 Discrepancy D5 withdrawn; D7 added
- What: D5 (mu/6 inconsistent with 0 elsewhere) was a misreading; the SI explains both entries.
  New D7: SI Fig. 9 axis labels are swapped relative to its caption (the caption and our
  computations agree). Counting D1-D4, D6 and D7, there are still six inconsistencies, now "in
  the published paper and its SI".

## D-020 Source of the SI file
- What: the publisher's SI file as archived by the Internet Archive (snapshot 2022-01-20),
  after PNAS (403), PMC (CAPTCHA, not bypassed), Europe PMC (not open access), IIASA PURE and the
  Kyushu portal failed. Content checked against the main text (identical T and stationary
  distribution). SHA-256 recorded in SI_EXTRACT.md.

## D-021 Read-offs from SI figures are digitized by script
- What: cycle counts in SI Fig. 8 are digitized from the vector PDF by
  experiments/digitize_si.py (line colors and hysteresis thresholds stated in the script), and
  the positions of the period labels in SI Fig. 9B are read from the rendered page and stored in
  that script. Both are approximate and are labelled as read-offs wherever they are used.

## D-022 B3: the default definition stays; other definitions are reported beside it
- What: the headline B3 value keeps the definition fixed before the SI was read (ratio of the
  mean honest share to the mean corrupt share, METRICS.md). The time with all umpires honest over
  the time with all umpires corrupt, and the majority-time ratio, are reported beside it from the
  same runs (rep_b3_diag).
- Why: switching the headline to the definition that matches 2.15 after seeing the result would
  be tuning the analysis to force a match (integrity rule 4). The SI does not state which
  definition the authors used, so both readings are reported and the question is left open.
- Alternatives: replace the headline value (rejected for the reason above); report only the
  default (rejected, because the Markov-type definition is the natural reading of a quantity
  compared with a Markov prediction).

## D-023 Release preparation: branch name, files kept out, history left as is
- What: (1) the default branch `master` was renamed to `main`, and `si-verification` was merged
  into it with `--no-ff`. (2) refs/ (paper and SI PDFs) was checked: it is gitignored and was never
  committed, so no history rewrite was needed. (3) logs/ (build logs with local Windows paths),
  results/quick/ and figures/quick/ (regenerated by `make quick` in a few minutes) were removed
  from the tree and gitignored. (4) The pre-SI result JSON files in results/pre_si/ were removed
  from the tree; they duplicate results/full/ except for runtimes and rep_markov.json and remain
  in the history at commit aef9a3f. The macros and hypothesis outcomes that
  make_changes_si.py needs are kept. (5) results/full/ (about 21 MB) is kept: it is the record of
  every reported number (R6) and lets `make numbers docs paper` run without the 17-minute
  pipeline. Main figures (PNG and PDF, about 6 MB) are kept: the README embeds one and the paper
  needs them to compile. (6) experiments/digitize_si.py now reuses the committed
  results/full/si_digitized.json when the SI PDF is absent, so a clone without refs/ can run
  `make all`. This changes no result.
- Why not rewrite history to drop the old logs: the logs contain only the local project path
  (the Windows user folder, which shows the author's name). Every result file records the git
  commit that produced it, and the documents cite commit aef9a3f; rewriting history would break
  those links. PUSH_INSTRUCTIONS.md gives the command if the author prefers to purge them.
- Personal files: the SOP sentences, the author notes, the CV entry and the project brief were
  first kept as deliverables listed in the brief. Superseded by D-026: they are now in private/
  and were removed from the history.

## D-024 Order of release steps
- What: the release tag v1.0.0, the CV entry and the push are done after Parts 2 and 3 of the
  release task (B3 wording in the paper, neutral wording), not in the middle of Part 1.
- Why: the tag should point to the final content. Tagging first and then changing the paper and
  documents would make v1.0.0 differ from what the README describes.

## D-025 Scope of the neutral-wording audit
- What: the paper sources, Markdown templates, SPEC.md, SI_EXTRACT.md and code comments now
  describe D1-D4, D6 and D7 as notation inconsistencies with evidence and our resolution. D5 is
  described only in CHANGES_SI.md and in this log (D-019) as our misreading, plus one reminder in
  Part 4 of the author notes, as the release task asks. The paper main text keeps one sentence on
  notation inconsistencies (Model section); the details are in the appendix. Internal LaTeX labels
  `app:typos` and `tab:typos` were renamed to `app:notes` and `tab:notation`.
- Not changed: DECISIONS.md and PROGRESS.md entries written earlier, CHANGES_SI.md history and
  results/pre_si/ keep the wording of the time, because they are dated logs and snapshots.
  The project brief was not edited. WORDING_AUDIT.md lists every replacement.
