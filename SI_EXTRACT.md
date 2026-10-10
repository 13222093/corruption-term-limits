# SI_EXTRACT.md: what the SI Appendix specifies, compared with the code

Source: Lee J-H, Iwasa Y, Dieckmann U, Sigmund K (2019), Supporting Information,
`refs/pnas.1900078116.sapp.pdf` (10 pages; PDF title "SI Appendix"; created 2019-06-06;
15,731,613 bytes; SHA-256 25f0e1315701019c13979184a5c1141cce53b1f050ca51867882e848998afb47).

How it was obtained (2026-10-10): the file was not in refs/. PNAS (www.pnas.org, HTTP 403),
the PMC copy (CAPTCHA, not bypassed), Europe PMC (API reply: "not open access"), IIASA PURE
(only the main article is deposited) and the Kyushu University portal (no files) did not provide
it. The publisher's own SI file was retrieved from the Internet Archive snapshot of
`https://www.pnas.org/content/pnas/suppl/2019/06/13/1900078116.DCSupplemental/pnas.1900078116.sapp.pdf`
taken 2022-01-20 (HTTP 200, application/pdf). Its content (title line "Supporting Information,
Lee et al. 10.1073/pnas.1900078116", the transition matrix and stationary distribution identical
to the main text) confirms that it is the SI of this article.

## Contents of the SI
- p.1-2 "Large populations": replicator analysis of the faces y1 = 1 and y1 = 0, transversal
  eigenvalues, fixed points OD+PD and OD+PC, invasion thresholds along the OC edge, the face
  x1 = x4 = 0 (SI Fig. 6), origin of the limit cycle for small exploration.
- p.2-3 "Rare exploration": derivation of T_H, T_C and the 10 x 10 matrix T, fixation
  arguments, stationary distribution, H:C ratio.
- p.3 "Cost-free information" (h = 0): 8-state chain, T, stationary distribution,
  H:C = 14 + 8N + 12M : 25.
- p.4-10 SI Figs. 1-10: corruption indices (1-4), isocline surface (5), flow on the face
  x1 = x4 = 0 (6), individual-based runs for other mu and s (7) and other M and s (8),
  mean-field amplitude, period and payoffs over (h, mu = nu) (9, 10).

**The SI does not describe the individual-based simulation procedure.** It states no update
order, no time unit, no rule for evaluating payoffs in a finite population and no run length or
averaging procedure for the reported ratio 2.15. The items below therefore separate what the SI
states, what it implies, and what remains a reconstruction.

## U1 to U4 and the related assumptions

Labels follow SPEC.md (U1: individual-based procedure, with assumptions A1-A4; U2: derivation
of T; U3: how 2.15 was computed; U4: parameters of SI Figs. 7-9). The task's four topics
(update scheme, payoff evaluation, time unit, derivation of T) are A1/A2, A3, A1 and U2.

| Item | What the SI says (location) | What the code does | Verdict |
|---|---|---|---|
| A4 exploration, players | "An exploration step leads a player with the same probability from the resident population to one of the three alternative strategies, which explains the factor 1/3" (p.2, rare-exploration section) | Exploring player switches uniformly to one of the 3 other strategies (`src/ibm.py`) | **identical** (test `test_player_exploration_goes_to_the_other_three_strategies`) |
| A4 exploration, umpires | nu is "the probability that one of the N umpires happens to switch to the alternative strategy at random (i.e., without considering a role model)" (p.2) | Exploring umpire flips its type; no role model | **identical** (test `test_umpire_exploration_flips_type_without_role_model`) |
| Exploration rates | "the corresponding exploration rate of the umpire population is nu = mu M / N = 5 mu" (SI Fig. 7 caption, p.7); "mu is the M-fold of the individual exploration rate" for the Markov chain (p.2) | mu, nu are per-individual probabilities per update; configs use nu = mu M / N | **identical** (test `test_umpire_exploration_rate_is_mu_M_over_N`) |
| Imitation rule | Not restated; main text gives the Fermi rule and hard imitation with ties at 1/2. The SI uses "the same probability of 1/2" for a tie (p.2) | Fermi rule, ties 1/2 | **identical** |
| A3 payoff evaluation | Not stated. Implied: "if a PC-dissident occurs in a population of PD-residents, the dissident does exactly as well as the residents ... [with] two PC-players ... PC-players have a higher average payoff" (p.2). This is true only if a player's co-player excludes itself (with self-play a single PC would already do better). Also "the relative frequency of OD ... (more precisely, the nearest multiple of 1/M)" (p.2) | Expected payoffs from counts; co-player drawn from the other M - 1 players; umpire serves two distinct players | **equivalent / supported** for the player part (test `test_single_neutral_dissident_payoffs`); umpire pair sampling not stated (**still reconstructed**, irrelevant in the limit and at all pure states) |
| A2 role model | Not stated. The 1/2 argument (p.2: "the next imitation step involving the dissident can lead with the same probability of 1/2 back ... or to a population with two PC-players") holds when the dissident is chosen as focal or as role model at equal rates, as in our scheme | Role model drawn from the other members of the focal's population | **consistent, still reconstructed** (test `test_pc_dissident_in_allPD_fixes_with_probability_half`: 0.5 in our IBM) |
| A1 update order and time unit | Not stated. SI Fig. 8 caption (p.8): "smaller population size or stronger selection accelerate the dynamics" (in the time units of the figure). SI Fig. 7 (p.7): time axes up to 2.2 x 10^8 with ~4 episodes per 10^5 units at the Fig. 1 setting | Random sequential updating, one individual from all M + N per elementary step; Fig. 1 time = elementary steps; 1 generation = M + N steps | **consistent and quantitatively supported, still not stated**: digitized SI Fig. 8 cycle counts per 5 x 10^6 units (results/full/si_digitized.json; values and comparison in CHANGES_SI.md Section 6) match our model at the same settings (results/full/rep_si_checks.json). A generation-based unit would change the counts by a factor of M + N |
| Neutral umpire fixation | "The probability that a dissident C-umpire can eventually replace the H-residents is given by the neutral fixation probability 1/N" (p.2) | Ties at 1/2 give neutral drift | **identical** (test `test_neutral_umpire_fixes_with_probability_one_over_N`) |
| U2 derivation of T | Full derivation (p.2-3): T_H, T_C, cross terms; the entry mu/6 because "a PC-dissident in a PD-population reaches fixation with probability 1/2"; a PD-dissident in allPC "cannot yield to PD"; neutral umpires 1/N; for h = 0, player mutants neutral throughout enter with mu/(3M) | Pre-SI: neutral player mutants were ignored (entry 0), so our derived T gave 0 instead of mu/6 at (4,2) | **different (our pre-SI derivation was incomplete on this point)**; fixed: `derive_transitions` now applies the SI rule (two-mutant comparison: 1/2, 0, or 1/M). Derived T now equals the printed T except D4, and reproduces the SI's h = 0 matrix and closed form exactly (tests) |
| Stationary distribution | SI p.2-3 gives the intermediate equations and the same result as the main text | Symbolic solution | **identical** |
| U3 how 2.15 was computed | Not stated. SI Fig. 7 shows runs whose time axis starts at 1.4 x 10^8 | Mean over 30 runs of y/(1-y) of time averages, 2 x 10^5 generations each | **still unverified**; see CHANGES_SI.md for the investigation of the gap |
| U4 SI Figs. 7-9 parameters | Fig. 7: mu in {1e-3, 1e-6}, s in {1e10, 10}, nu = 5 mu, others as Fig. 1A, B. Fig. 8: M in {3000, 2000, 1000}, N = M/5, s in {10, 1, 0.3}, others as Fig. 1C, D. Fig. 9: h in [0, 0.35] and mu = nu in [0, 0.08] (mean field), others as Fig. 1A, B | Not used before | **resolved**; used for new checks (rep_si_checks) |

Summary for U1: the SI-faithful model is the reconstruction. Every rule the SI states is
satisfied; nothing the SI states contradicts it. Update order, role-model sampling and umpire
pair sampling remain unstated and stay as documented assumptions.

## Notation inconsistencies D1 to D4, D6 and D7

| ID | Claim (pre-SI) | Evidence in the SI | Verdict |
|---|---|---|---|
| D1 | Methods prints Q(y) = y1 Q_C + (1 - y1) Q_H, although y1 is the honest fraction | SI p.1: "When all umpires are honest, i.e., y1 = 1"; "When all umpires are corrupt, i.e., y1 = 0". The SI does not restate Q(y) | **reading supported** (y1 is the honest fraction; the printed weighting exchanges Q_H and Q_C) |
| D2 | Methods calls the honest mixed state "OD+PD (a mixture of OD and PC)" | SI p.2 uses the same label ("OD+PD (the last because of the mutual invasibility of OD and PC)"), but SI p.1 derives the fixed point (0, 0, h/(f+A), (f+A-h)/(f+A)) on the edge OD-PD from mutual invasion of OD and PD | **reading supported** (the state mixes OD and PD; the label "PC" also appears in the SI) |
| D3 | Fig. 3 caption: "(c-B)/(A-B) < (c-B-h)/(b-B-f) or not ... state 8 or 9, respectively" lists the states in the opposite order to the panels | SI p.1: along the OC edge the OD threshold is (c-B)/(A-B) and the PD threshold (c-B-h)/(b-B-f); "see Fig. 3A, where PD can invade in this interval, and Fig. 3B, where OD can invade instead". For A = 2 the inequality holds and PD (state 9) is visited | **reading supported** (the SI agrees with the panels and with our numerics) |
| D4 | Printed T has no entry for allOD(H) -> allOD(C) | SI p.2: "In the states (allPD,allH), (allOD,allH), and (OD+PD,allH), C-umpires can invade and take over", but the SI's list of cross terms (T4,9, T5,8, T7,2, T10,2) and its matrix omit T3,8. In the h = 0 matrix (SI p.3) the analogous entry is present | **reading supported** (the SI text and its matrix differ in the same way); no effect on the stationary distribution |
| D6 | Fig. 3C, D are labeled as the orange orbit (mu = nu = 1e-4) but match mu = nu = 0.02 | The SI says nothing about Fig. 3C, D. SI Fig. 9B (mean-field periods) shows periods near 140 at h = 0.1, mu = nu = 0.02 and periods beyond the 2000 contour at very small mu, consistent with our periods (136.5 at 0.02, 9437 at 1e-4) | **confirmed (indirect support)** |
| D7 (new) | - | SI Fig. 9 caption: "information cost h (horizontal axes) and the exploration rates mu = nu (vertical axes)", but the panels label the horizontal axis "Exploration rate" (0-0.35) and the vertical axis "Information cost" (0-0.08). The ranges, the damped region above mu = nu of about 0.06 at h = 0.1 (our Hopf point 0.0616) and the period contours follow the caption | **new notation inconsistency** (panel axis labels exchanged relative to the caption; we follow the caption) |

## Other SI content that bears on the model
- Mean-field periods (SI Fig. 9B): at h = 0.1 the labelled contours (about 200 near mu = nu
  0.01, 150 near 0.017, 120 near 0.03, 100 near 0.04) agree with our replicator-mutator periods;
  see rep_si_checks.json for a point-by-point comparison at the label positions.
- Cost-free information (SI p.3): the 8-state chain and its closed form are reproduced exactly
  by our derivation (tests `test_cost_free_chain_matches_SI`,
  `test_cost_free_stationary_distribution_and_ratio`).
- SI p.1 describes, for small exploration, an orbit along the OC edge "along which y1 ...
  decreases" because corrupt umpires gain more from (OC, PD) pairs than they lose; this is the
  mechanism behind our invasion-threshold explanation of D3 and behind the rho_c formula.
- SI p.1 contains a small notation inconsistency: "For (OC,PD) pairs, C-umpires do less well ... For (OC,PD) pairs,
  C-umpires do better"; from the income rules the first pair must be (OC, PC). This has no
  consequence for the model and is not counted as a discrepancy.
