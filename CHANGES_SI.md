<!-- Generated from docs_src/CHANGES_SI.md.in by experiments/render_docs.py; edit the template, not this file. -->
# CHANGES_SI.md: what changed after verifying the model against the SI

Branch: `si-verification`. Source: SI Appendix of Lee et al. (2019),
`refs/pnas.1900078116.sapp.pdf` (how it was obtained: SI_EXTRACT.md). All numbers below are
generated from `results/` (old values from `results/pre_si/`, the snapshot taken before the
rerun).

## 1. Summary
- **The SI does not specify the individual-based procedure** (update order, time unit,
  finite-population payoff rule, averaging of the reported ratio). It states several rules that
  the reconstruction already satisfies, and its figures support the reconstructed time unit
  quantitatively. The SI-faithful model is therefore the reconstruction: the default
  `ibm_variant: si` and the alternative `ibm_variant: reconstructed` run the same kernel and gave
  identical results for every benchmark (identical: yes).
- **The derivation of the Markov transition matrix changed.** The SI gives the fixation rule for
  neutral player mutants (probability 1/2 if two mutants already do better, 0 if they do worse,
  1/M if neutral throughout). Our pre-SI derivation set such entries to 0. With the SI rule the
  derived matrix equals the printed one except for discrepancy D4, and the SI's cost-free
  (h = 0) chain and its closed form are reproduced exactly. The closed form (19N + 87):109 is
  unchanged (2.541 for N = 10).
- **Discrepancy D5 was withdrawn** (our misreading). D1, D2, D3, D4 and D6 were confirmed; a new
  inconsistency D7 (SI Fig. 9 axis labels) was found.
- **No simulation result and no hypothesis outcome changed**, because the simulated process is
  unchanged; the full pipeline was rerun and reproduced every simulated value (table in
  Section 3). Only two diagnostics of the derived Markov chain changed (`MarkovNdiff`,
  `MarkovRatioFinM`), both as expected from the corrected derivation.
- **The B3 gap closes under one plausible definition of the time average** (time with all
  umpires honest over time with all umpires corrupt: 2.134 [2.102,
  2.165], which contains 2.15), and remains under the literal definition used before
  (mean honest share over mean corrupt share: 2.030 [2.003,
  2.057]). The SI does not say which definition was used (U3).

## 2. Which results depend on the individual-based model or the Markov chain



Derived from the code (every IBM result goes through `src.ibm.run_ibm`, directly or via
`src.runners.ibm_replicate`; the Markov chain lives in `src/rare_exploration.py`).

| Result file | Section | Depends on IBM / Markov chain | Mean-field only parts |
|---|---|---|---|
| rep_b1b2 | B1, B2 | no | all |
| rep_fig3 | Fig. 3 orbits, D3, D6 | no | all |
| rep_shrinkage | orbit shrinkage, Hopf in mu | no | all |
| rep_markov | B3 Markov ratio, derived T | Markov chain (T derivation) | n/a |
| rep_b3 | B3 simulated ratio, scan, SE check | IBM (small) | none |
| rep_b4_small | B4 cycles (Fig. 1) | IBM (small) | none |
| rep_b4_large | B4 damped oscillations (Fig. 2A) | IBM (large) | exact mean field of the IBM, eigenvalues |
| rep_validation | IBM vs exact mean field (Fig. 10A) | IBM (large rates) | reference ODE |
| ext_bif | SNIC, rho_c, two-parameter diagram | no | all |
| ext_e1 | rho x h | IBM part (ibm_small) | meanfield, critical |
| ext_e2 | rho x kappa (V1-V3), V1 equivalence | IBM part (ibm_small) | meanfield_V1..V3 |
| ext_e3 | time series | IBM part (ibm_small series) | meanfield series |
| ext_e4 | H1, H2 finite population | IBM (small and large) | none |
| ext_e5 | V2 hysteresis, scan | IBM part (ibm_small two starts) | hysteresis, fold curve, scan |
| ext_e5b | V2 follow-up | IBM part (ibm two starts) | maps, sweeps |
| ext_e6 | V3 delay stability | no | all |
| sens_oat | sensitivity | IBM part (ibm_large_s, s identity check) | meanfield OAT |
| sens_pulse | pulses vs continuous | IBM part (ibm_small) | meanfield |
| sens_altA | A = 0.7 | IBM part (ibm_small) | meanfield, critical |
| sens_p0 | p0 < 1 | IBM part (ibm_small) | meanfield, critical |
| sens_finite | finite size | IBM | none |
| sens_explo | other exploration rates | no | all |
| sens_numerics | tolerance and grid checks | no | all |
| sens_se | SE vs replicates | IBM | none |

Figures with IBM or Markov content: Fig. 1 (fig01), Fig. 2 panel A (fig02), Fig. 3 (fig03),
Fig. 5 panel C (fig05), Fig. 6 panels D-F (fig07 file), Fig. 7 panels D-F (fig06 file),
Fig. 8 panel E (fig08), Fig. 10 (fig10), Fig. S1 bottom row, Fig. S4 (new). Mean-field only: Fig. 4 (fig04),
Fig. 9 (fig09), Fig. S2, Fig. S3, and the mean-field panels of the figures above.


Mean-field results (ODE, DDE, continuation, all hypothesis evidence labelled "mean field") do not
depend on U1 to U4. This was confirmed by the inventory above and by the rerun: every mean-field
number is identical.

## 3. Old and new values

### Finite-population numbers

78 finite-population quantities compared; 2 changed.

| Quantity (macro) | Meaning | Old (pre-SI) | New (SI-verified) | Abs. change |
|---|---|---|---|---|
| `BfourCorrupt` | large IBM late mean corrupt | 0.541 | 0.541 | 0 |
| `BfourOC` | large IBM late mean OC | 0.534 | 0.534 | 0 |
| `BfourOD` | large IBM late mean OD | 0.050 | 0.050 | 0 |
| `BfourPC` | large IBM late mean PC | 0.186 | 0.186 | 0 |
| `BfourPD` | large IBM late mean PD | 0.229 | 0.229 | 0 |
| `BthreeDouble` | H:C with doubled window | 2.032 | 2.032 | 0 |
| `BthreeGens` | generations per replicate | 200000 | 200000 | 0 |
| `BthreeRatio` | IBM H:C at mu=1e-3 | 2.030 | 2.030 | 0 |
| `BthreeRatioB` | IBM H:C at mu=3e-4 | 2.318 | 2.318 | 0 |
| `BthreeRatioC` | IBM H:C at mu=1e-4 | 2.459 | 2.459 | 0 |
| `BthreeSE` | SE of ybar at 30 reps (B3) | 0.0010 | 0.0010 | 0 |
| `BurnLarge` | burn-in, large IBM | 1000 | 1000 | 0 |
| `BurnSmall` | burn-in, small IBM | 5000 | 5000 | 0 |
| `EpisodesSteps` | episodes per 1e5 steps | 6.0 | 6.0 | 0 |
| `FinLargeTen` | finite M large rho=0.1 | 0.767 | 0.767 | 0 |
| `FinLargeZero` | finite M large rho=0 | 0.616 | 0.616 | 0 |
| `FinMmax` | largest M | 400 | 400 | 0 |
| `FinSmallZero` | finite M small rho=0 | 0.673 | 0.673 | 0 |
| `FineGridMaxOff` | fine grid offset | 0.0012 | 0.0012 | 0 |
| `FineGridStep` | fine grid step | 0.00125 | 0.00125 | 0 |
| `HfourIncIBM` | IBM pairs increasing | 29 | 29 | 0 |
| `HfourPairsIBM` | IBM pairs | 32 | 32 | 0 |
| `HfourYZeroMax` | IBM honesty rho=0 max over h | 0.669 | 0.669 | 0 |
| `HfourYZeroMin` | IBM honesty rho=0 min over h | 0.665 | 0.665 | 0 |
| `HoneEpLMax` | H1 ibm_large episodes max | 0.00 | 0.00 | 0 |
| `HoneEpLZero` | H1 ibm_large episodes rho=0 | 10.07 | 10.07 | 0 |
| `HoneEpSMax` | H1 ibm_small episodes max | 0.29 | 0.29 | 0 |
| `HoneEpSZero` | H1 ibm_small episodes rho=0 | 3.63 | 3.63 | 0 |
| `HoneRhoMaxIBM` | largest IBM rho | 0.3 | 0.3 | 0 |
| `HoneYLMax` | H1 ibm_large ybar rho max | 0.876 | 0.876 | 0 |
| `HoneYLZero` | H1 ibm_large ybar rho=0 | 0.458 | 0.458 | 0 |
| `HoneYSMax` | H1 ibm_small ybar rho max | 0.978 | 0.978 | 0 |
| `HoneYSZero` | H1 ibm_small ybar rho=0 | 0.669 | 0.669 | 0 |
| `HthreeBonf` | Bonferroni verdict | holds | holds | same |
| `HthreeMaxDiff` | max |diff| | 0.0073 | 0.0073 | 0 |
| `HthreeNexcl` | tests whose CI excludes 0 | 2 | 2 | 0 |
| `HthreeNtests` | equivalence tests | 15 | 15 | 0 |
| `HtwoDCLZero` | H2 ibm_large min coop in episode rho=0 | 0.694 | 0.694 | 0 |
| `HtwoDCSTen` | H2 small min coop rho=0.1 | 0.643 | 0.643 | 0 |
| `HtwoDCSThirty` | H2 small min coop rho=0.3 | 0.522 | 0.522 | 0 |
| `HtwoDCSZero` | H2 ibm_small min coop in episode rho=0 | 0.262 | 0.262 | 0 |
| `HtwoDYSTen` | H2 small peak corruption rho=0.1 | 0.910 | 0.910 | 0 |
| `HtwoDYSThirty` | H2 small peak corruption rho=0.3 | 0.888 | 0.888 | 0 |
| `HtwoDYSZero` | H2 small peak corruption rho=0 | 0.965 | 0.965 | 0 |
| `HtwoPCLZero` | H2 ibm_large PC rho=0 | 0.197 | 0.197 | 0 |
| `HtwoPCSTen` | H2 small PC rho=0.1 | 0.050 | 0.050 | 0 |
| `HtwoPCSThirty` | H2 small PC rho=0.3 | 0.006 | 0.006 | 0 |
| `HtwoPCSZero` | H2 ibm_small PC rho=0 | 0.210 | 0.210 | 0 |
| `HtwoRecLZero` | H2 ibm_large recovery rho=0 | 84.3 | 84.3 | 0 |
| `HtwoRecSTen` | H2 small recovery rho=0.1 | 32.7 | 32.7 | 0 |
| `HtwoRecSThirty` | H2 small recovery rho=0.3 | 23.3 | 23.3 | 0 |
| `HtwoRecSZero` | H2 ibm_small recovery rho=0 | 88.1 | 88.1 | 0 |
| `LargeReps` | large IBM replicates (B4) | 10 | 10 | 0 |
| `MSmall` | players, small setting | 50 | 50 | 0 |
| `MarkovNdiff` | number of differing entries | 4 | 2 | 2 |
| `MarkovRatio` | Markov H:C at N=10 | 2.541 | 2.541 | 0 |
| `MarkovRatioFinM` | Markov, M = 50, SI fixation rules (1/M for neutral players) | 2.540 | 2.541 | 0.001 |
| `NSmall` | umpires, small setting | 10 | 10 | 0 |
| `NeutralMaxDev` | max |ybar - (nu+rho)/(2nu+rho)| for rho>=0.05 (large IBM) | 0.008 | 0.008 | 0 |
| `Nreps` | IBM replicates per condition | 30 | 30 | 0 |
| `PulseIBMCont` | IBM continuous rho=0.03 | 0.802 | 0.802 | 0 |
| `PulseIBMFull` | IBM pulse tau=1 rho=0.03 | 0.899 | 0.899 | 0 |
| `SEFifty` | SE at n=50 | 0.0014 | 0.0014 | 0 |
| `SEFive` | SE at n=5 | 0.0042 | 0.0042 | 0 |
| `SEThirty` | SE of ybar at n=30 | 0.0016 | 0.0016 | 0 |
| `SLargeTen` | large IBM honesty rho=0.1 | 0.749 | 0.749 | 0 |
| `SLargeTenHigh` | same at 1.2 s | 0.749 | 0.749 | 0 |
| `SLargeTenLow` | same at 0.8 s | 0.749 | 0.749 | 0 |
| `ValMA` | validation M | 500 | 500 | 0 |
| `ValMB` | validation M | 2000 | 2000 | 0 |
| `ValMC` | validation M | 8000 | 8000 | 0 |
| `ValMD` | validation M | 32000 | 32000 | 0 |
| `ValRmsA` | validation RMS | 0.113 | 0.113 | 0 |
| `ValRmsB` | validation RMS | 0.047 | 0.047 | 0 |
| `ValRmsC` | validation RMS | 0.025 | 0.025 | 0 |
| `ValRmsD` | validation RMS | 0.011 | 0.011 | 0 |
| `WinLarge` | window, large IBM | 5000 | 5000 | 0 |
| `WinSmall` | window, small IBM (generations) | 100000 | 100000 | 0 |

### Hypothesis outcomes

0 of 6 outcomes changed.

| Hypothesis | Old outcome | New outcome | Flipped? |
|---|---|---|---|
| H1 | supported | supported | no |
| H2 | not supported | not supported | no |
| H3 | supported | supported | no |
| H4 | substitutes (mean field and IBM agree) | substitutes (mean field and IBM agree) | no |
| H5 | mixed | mixed | no |
| H6 | not supported | not supported | no |

### New quantities added on this branch

`BthreeMajority`, `BthreePerRepFrac`, `BthreePerRepSD`, `BthreePure`, `DiagBurn`, `DiagExploreAny`, `DiagPairStep`, `DiagRoleAny`, `DiagSelTen`, `DiagSelThousand`, `DiagSelfPayoff`, `DiagStartOC`, `EightMaxDevStrong`, `EightMaxDevWeak`, `EightMinDevWeak`, `HZeroIBMA`, `HZeroIBMB`, `HZeroPred`, `LongRunMax`, `LongRunMean`, `LongRunN`, `LongRunSD`, `LongRunSteps`, `NineDevFourHundred`, `NineMaxDev`, `NineMinDev`, `NineNpoints`, `OurEightA`, `OurEightAMax`, `OurEightAMin`, `OurEightB`, `OurEightBMax`, `OurEightBMin`, `OurEightD`, `OurEightDMax`, `OurEightDMin`, `OurEightE`, `OurEightEMax`, `OurEightEMin`, `OurEightG`, `OurEightGMax`, `OurEightGMin`, `OurEightH`, `OurEightHMax`, `OurEightHMin`, `RecBthreeRatio`, `SIBthreeRatio`, `SIEightA`, `SIEightB`, `SIEightD`, `SIEightE`, `SIEightG`, `SIEightH`, `SIVariantsIdentical`, `ShortRunFrac`, `ShortRunMean`, `ShortRunN`, `ShortRunQhi`, `ShortRunQlo`, `ShortRunSD`



`MarkovNdiff` counts the entries in which our derived transition matrix differs from the printed
one (4 before: D4 and the former D5; 2 now: D4 only). `MarkovRatioFinM` is the ratio of the
derived chain for M = 50 with neutral player mutants fixing at 1/M. Before the SI, those entries
were partly missing and the value differed slightly from the closed form; with the SI rules it
equals (19N + 87):109 = 2.541. No conclusion depends on either quantity.

## 4. Discrepancies D1 to D7

| ID | Status | Evidence from the SI |
|---|---|---|
| D1 Q(y) weighting | confirmed | SI p.1 defines y1 = 1 as all umpires honest |
| D2 OD+PD called "OD and PC" | confirmed | SI p.1 derives the OD-PD fixed point; SI p.2 repeats the slip |
| D3 Fig. 3 caption "respectively" | confirmed | SI p.1: "Fig. 3 A, where PD can invade ... Fig. 3 B, where OD can invade instead" |
| D4 T omits allOD(H) -> allOD(C) | confirmed, strengthened | SI p.2 says corrupt umpires invade (allOD, allH); T still omits it |
| D5 mu/6 vs 0 for neutral mutants | **withdrawn** | SI p.2 explains both entries (two-mutant rule) |
| D6 Fig. 3C, D labelling | confirmed (indirect) | SI Fig. 9B periods: about 140 at mu = nu = 0.02, beyond 2000 at very small mu |
| D7 SI Fig. 9 axis labels | **new** | Caption: h horizontal, mu = nu vertical; panels: swapped labels |

## 5. Did the B3 gap close?

Published simulated ratio 2.15; Markov limit 2.541. Each check changes one possible
cause; none changes the default model.

| Check | Ratio (95% CI) | Reading |
|---|---|---|
| Default: mean honest / mean corrupt, 30 runs of 200000 generations | 2.030 [2.003, 2.057] | gap remains |
| Same runs, time with honest majority / corrupt majority | 2.110 [2.080, 2.139] | gap nearly closes |
| Same runs, time with all honest / all corrupt umpires | 2.134 [2.102, 2.165] | **closes (CI contains 2.15)** |
| Burn-in 50000 instead of 5000 generations | 2.003 [1.976, 2.031] | no effect |
| Start from all OC instead of all OD | 2.030 [2.003, 2.056] | no effect |
| Imitation intensity s = 1000 | 2.029 [2.003, 2.056] | no effect (hard imitation already) |
| Imitation intensity s = 10 | 2.422 [2.387, 2.457] | moves away from 2.15 |
| Exploration may keep the own strategy | 2.512 [2.465, 2.558] | moves away |
| Role model may be oneself | 2.010 [1.988, 2.033] | no closing |
| Payoffs include self-play | 2.018 [1.993, 2.043] | no closing |
| One player and one umpire per step | 1.266 [1.255, 1.278] | far off (contradicts the SI's nu = mu M / N) |
| Run length: 10 runs of 2.2e8 steps (SI Fig. 7 length) | mean 2.037, SD 0.025, max 2.075 | a long run with the default definition does not give 2.15 |
| Run length: 300 windows of 1e5 steps (Fig. 1A length) | mean 2.39, SD 1.13, 5-95%: 1.12-4.87; 48% reach 2.15 | a short window is too noisy to discriminate |
| Per-replicate spread (2 x 10^5 generations) | SD 0.077; 3% of replicates reach 2.15 | |

Conclusion: the remaining explanation is the definition of the time average. If the authors
counted the time spent with all umpires honest against the time with all umpires corrupt (the
quantity their Markov chain predicts), our simulation agrees with their 2.15. If they used the
ratio of mean shares over a long run, our model gives 2.037, and the difference would point
to an unpublished detail of their update procedure. Their own SI does not decide this.

## 6. New checks against the SI figures
- SI Fig. 8 (individual-based, M = 1000 to 3000, s = 10 and 1, 5 x 10^6 time units): cycle counts
  digitized from the SI versus our model at the same settings (4 replicates): A 17 vs
  18.0, D 25 vs 25.8, G 53 vs 51.2 (s = 10; at most
  6% apart); B 6 vs 6.0, E 6 vs 8.2,
  H 14 vs 17.2 (s = 1; our counts 0% to 38%
  higher; each SI panel is a single run). A generation-based time unit would change these counts
  by a factor of M + N (1200 to 3600). This supports our time unit (A1), which the SI does not state.
- SI Fig. 9B (mean-field periods): at 8 label positions our periods are within
  2.5% to 5.6% of the labels, except the label 400 (20%),
  which sits where the contours crowd.
- Cost-free information (SI p.3): the closed form predicts H:C = 27.76 for N = 10,
  M = 50. Our simulation gives 7.90 [7.76, 8.04] at mu = 0.001 and
  15.32 [14.80, 15.85] at mu = 0.0003, rising toward the limit as
  exploration becomes rarer (the slow 1/M transitions make convergence slow).

## 7. Figures
No figure changed its qualitative message: the individual-based figures (Figs. 1, 2A, 3, the
finite-population panels of Figs. 5-8, Fig. 10, Fig. S1) were regenerated from identical results.
A new supplementary figure (Fig. S4, `figures/figS4_si_checks`) shows the B3 investigation and the
comparisons with SI Figs. 8 and 9B.
