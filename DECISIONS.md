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
- Why: CLAUDE.md asks for 3.11; 3.12 is what is installed, conda is not installed, and nothing in
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
- Why: CLAUDE.md integrity rule 1. Access attempts: PMC (CAPTCHA, not bypassed), PNAS (HTTP 403),
  IIASA PURE (bot protection).

## D-010 Default delay in V3
- What: continuous rotation: T_lag = 1/rho (mean term length). Pulse rotation: T_lag = T.
  E6 varies T_lag independently.
- Why: CLAUDE.md says "T_lag = one term"; under continuous rotation the mean term is 1/rho.

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

## D-016 Literature search (CLAUDE.md Section 13)
- What: web searches (2026-10-10) for evolutionary-game models of corruption with rotation, term
  limits or turnover of enforcers. Found none that model rotation of enforcers in an
  evolutionary game. Related: Lee et al. 2015 (JTB, enforcer education), Liu, Chen and Szolnoki
  2019 (M3AS, corrupt enforcers), Shi et al. 2023 and Zhou et al. 2023 (AMC, supervision of
  umpires), Abbink 2004 (experimental staff rotation), Ferraz and Finan 2011 (empirical term
  limits). The paper says "to our knowledge" and lists these.
