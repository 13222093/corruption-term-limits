# SPEC.md: model specification with source locations

Source of truth: Lee J-H, Iwasa Y, Dieckmann U, Sigmund K (2019) "Social evolution leads to
persistent corruption", PNAS 116(27):13276-13281, doi:10.1073/pnas.1900078116.
File: `refs/Social evolution leads to persistent corruption.pdf` (6 pages, scanned image; read
visually page by page at 150-300 dpi). Page numbers below are journal pages (13276 = p.1).

Abbreviations: "Main p.13277 col.2" = journal page 13277, right column.
"SI" = SI Appendix (`refs/pnas.1900078116.sapp.pdf`, obtained on branch si-verification; see Section 0 and SI_EXTRACT.md).

## 0. Availability of sources

| Source | Status |
|---|---|
| Main text PDF | Available in refs/. All equations below were read from it. |
| SI Appendix (pnas.1900078116.sapp.pdf) | AVAILABLE since 2026-10-10 (branch si-verification): refs/pnas.1900078116.sapp.pdf, 10 pages, obtained from the Internet Archive copy of the publisher's file (DECISIONS.md D-020). Read in full; see SI_EXTRACT.md. |

Status of the items that depended on the SI (details in SI_EXTRACT.md):
- U1. Individual-based update procedure. **The SI does not describe it.** Still reconstructed
  (A1-A4 below), but now checked against everything the SI states: A4 verified (SI p.2);
  A3 player part supported (SI p.2 single-dissident argument); A1 time unit supported
  quantitatively by SI Fig. 8 (cycle counts) and qualitatively by its caption; A2 consistent
  with SI p.2. No SI statement contradicts the reconstruction.
- U2. Derivation of T. **Verified from the SI** (p.2-3), including the fixation rules for neutral
  mutants; our derivation now follows them and reproduces the printed T except D4, and the SI's
  h = 0 chain exactly.
- U3. How 2.15 was computed. **Still unverified**: the SI does not say. SI Fig. 7 shows runs
  extending beyond 2.2 x 10^8 time units.
- U4. Parameters of SI Figs. 7-9. **Resolved** (SI Fig. captions; listed in SI_EXTRACT.md).

## 1. Players, umpires, strategies

- Donation game, benefit b, cost c, c < b. Main p.13277 col.1, Table A.
- Fee f paid by each participating player to the umpire; f < b - c. Main p.13277 col.1, Table B.
- Honest umpire fines each defector A > c. Main p.13277 col.1.
- Corrupt umpire takes bribe B from each defector instead of fining, B < c. Main p.13277 col.1, Table C.
- Prudent players pay h to learn the umpire type. PD drops out if the umpire is honest. PC drops
  out if the umpire is corrupt. Main p.13277 col.2 (paragraph "To sum up").
- Strategy order: OC, PC, OD, PD (x1..x4). Umpire types H, C (y1, y2). Main p.13277 col.2;
  Methods p.13280 col.2.
- Populations: M players, N umpires; counts M1..M4, N1, N2. Main p.13277 col.2.

## 2. Payoff matrices (Methods, p.13280 col.2; verified at 300 dpi)

Row player payoff against column player, order (OC, PC, OD, PD).

Q_H (all umpires honest):
```
OC: b-c-f    b-c-f    -c-f     0
PC: b-c-f-h  b-c-f-h  -c-f-h  -h
OD: b-f-A    b-f-A    -f-A     0
PD: -h       -h       -h      -h
```
Q_C (all umpires corrupt):
```
OC: b-c-f      0    -c-f       -c-f
PC: -h        -h    -h         -h
OD: b-f-B      0    -f-B       -f-B
PD: b-f-B-h   -h    -f-B-h     -f-B-h
```
All signs agree with CLAUDE.md Section 4. No discrepancy.

## 3. Umpire income (Methods, p.13280 col.2)

- Honest: 2f, except 0 if at least one PD among the two players.
- Corrupt: 0 if at least one PC among the two players; otherwise 2f plus one B per defector
  (OD or PD) among the two players.
- Reported (Methods p.13281 col.1): P_H(x) - P_C(x) = 2f(x2 - x4)(1 + x1 + x3) - 2B(x3 + x4)(1 - x2).
- Our derivation (verified by sympy and by brute-force pair enumeration in tests/test_payoffs.py):
  P_H = 2f(1 - x4)^2, P_C = 2f(1 - x2)^2 + 2B(x3 + x4)(1 - x2). Their difference equals the
  reported expression on the simplex (uses 2 - x2 - x4 = 1 + x1 + x3).

## 4. Inequalities (Main p.13277 col.2, Eqs. 1-4)

1. f + h < b - c
2. c + h < A
3. B + h < c
4. h < sqrt(f (f + B))   (confirmed: geometric mean of f and f + B; CLAUDE.md guess correct)

At base parameters: 0.3 < 0.5; 0.6 < 2; 0.3 < 0.5; 0.1 < 0.2828. All hold. Checked in
src/params.py (`check_inequalities`).

## 5. Replicator-mutator equations (Methods p.13281 col.1, "Large-Population Limit")

```
dx_i/dt = x_i [ sum_k Q_ik(y) x_k - Qbar ] - mu x_i + mu (1 - x_i)/3,  i = 1..4
dy1/dt  = y1 (1 - y1) [P_H(x) - P_C(x)] - nu y1 + nu (1 - y1)
Qbar    = sum_ik x_i Q_ik(y) x_k
```
State space S = Delta_4 x [0, 1].

DISCREPANCY D1 (typo in the PDF itself, not only PMC): the PDF prints
Q(y) = y1 Q_C + (1 - y1) Q_H. With y1 the honest fraction (y1 = 1 at fixed point 5 with Q_H
equilibrium x = (0, 0, h/(f+A), (f+A-h)/(f+A)) in Fig. 2 caption; y1 = 0 at fixed point 10 with
the Q_C equilibrium; dy1/dt uses P_H - P_C), the printed weighting is inconsistent.
RESOLUTION: Q(y) = y1 Q_H + (1 - y1) Q_C. Evidence: (a) Fig. 2 caption fixes y1 = 1 for the
honest simplex; (b) B1 and B2 (text p.13278 col.2) hold only with this reading (verified in
tests/test_fixed_points.py, which also shows the printed reading fails B1).
See DECISIONS.md D-001.

## 6. Fixed points and edges (Main p.13278, Fig. 2 and caption)

- Eight homogeneous states are fixed points of the replicator equations (mu = nu = 0).
- Edge x = (1, 0, 0, 0), y1 in [0, 1] is a line of fixed points (OC with either umpire type earn
  equally: P_H = P_C = 2f).
- Fixed point 5: x = (0, 0, h/(f+A), (f+A-h)/(f+A)), y1 = 1 (OD+PD mixture, honest umpires).
- Fixed point 10: x = (0, (f+B-h)/(f+B), h/(f+B), 0), y1 = 0 (OD+PC mixture, corrupt umpires).
- B1 (text p.13278 col.2): all umpires corrupt: OD -> h/(f+B), PC -> (f+B-h)/(f+B), OC and PD vanish.
- B2 (text p.13278 col.2): all umpires honest: OC -> 1.
- Condition 4 guarantees honest umpires can invade fixed point 10.

DISCREPANCY D2: Methods p.13281 col.1 calls the honest mixed state "OD+PD (a mixture of OD and PC)".
The Fig. 2 caption and Q_H show it is a mixture of OD and PD. Resolution: OD+PD.

## 7. Exploration rates and orbit shrinkage (Fig. 3, p.13279)

- Fig. 3A, B: start y1 = 1, x1 = x4 = 0.1, x2 = x3 = 0.4; mu = nu in {0.0001 (orange), 0.02
  (violet), 0.07 (blue)}; A = 2 (panel A), A = 0.7 (panel B); other parameters as Fig. 1A, B
  (b = 1, c = 0.5, f = B = 0.2, h = 0.1).
- With increasing exploration the limit cycle shrinks and becomes a stable fixed point reached by
  damped oscillations.
- Fig. 3C, D: orange orbit in A, time axis 0-400. Read-off (approximate, by eye): period about
  135-140 time units; OC peaks about 0.93; PC peaks about 0.70; PD peaks about 0.45; OD peaks
  about 0.27; honest fraction minimum about 0.05-0.10.
- Text in caption: "Depending on whether (c-B)/(A-B) < (c-B-h)/(b-B-f) or not, the limit cycle
  leaves the edge where all players are OCs to visit the absorbing state 8 or 9, respectively".
  At A = 2: 0.167 < 0.333 (inequality holds); at A = 0.7: 0.6 > 0.333. The figure shows the
  A = 2 orbit passing near 9 and the A = 0.7 orbit near 8, which is the reverse of the literal
  "respectively". DISCREPANCY D3 (text vs figure), resolved numerically in Phase 2 and CONFIRMED
  by the SI (p.1: "see Fig. 3 A, where PD can invade in this interval, and Fig. 3 B, where OD can
  invade instead").

## 8. Individual-based model (Main p.13277 col.2; Methods p.13280 col.2 "Dynamics"; Fig. 1)

Stated in the main text:
- Each individual updates by exploration with small probability mu (players) or nu (umpires),
  choosing another strategy at random, or by imitation.
- Imitation: X imitates randomly chosen role model Y with probability
  Pr(X -> Y) = [1 + exp(s (P_X - P_Y))]^-1, s >= 0. Hard imitation in the limit s -> infinity
  (1 if P_Y > P_X, 0 if P_Y < P_X, 1/2 if equal).
- Payoffs are the average payoffs, functions of the counts M1..M4, N1, N2 (p.13277 col.2).
- Fig. 1 A, B: M = 50, N = 10, mu = 0.001, nu = 0.005, s = 10^10 (confirmed: printed as 10^10 with
  superscript); time axis 2-3 x 10^5. Fig. 1 C, D: M = 5000, N = 1000, mu = 0.01, nu = 0.05,
  s = 0.3; time axis 0-5 x 10^6. Caption: "new strategies enter both populations through
  exploration at the same rate" (M mu = N nu = 0.05 and 50).
- Fig. 1 read-offs (approximate, by eye): A, B show about 7 corruption episodes per 10^5 time
  units. C, D: after the transient, OC about 0.5, PC about 0.2, PD about 0.2-0.25, OD about 0.05,
  corrupt fraction about 0.50-0.55.

U1: the SI does not specify the procedure. Status of each assumption after reading the SI
(DECISIONS.md D-003 to D-006, D-017; SI_EXTRACT.md):
- A1. Asynchronous random sequential updating: each elementary step picks one individual uniformly
  from all M + N individuals. Time is measured in elementary steps for comparison with Fig. 1
  (and also reported in generations, 1 generation = M + N steps). STILL RECONSTRUCTED (not stated
  in the SI) but SUPPORTED: SI Fig. 7 caption (nu = mu M / N, equal entry rates), SI Fig. 8
  caption (smaller populations accelerate the dynamics) and the digitized SI Fig. 8 cycle counts,
  which our model reproduces at the same settings.
- A2. Role model drawn uniformly from the other individuals of the same population. STILL
  RECONSTRUCTED; consistent with the SI p.2 argument (a neutral dissident's next imitation step
  goes either way with probability 1/2).
- A3. Expected payoffs from current counts. A player's co-player is drawn from the other M - 1
  players; its umpire is honest with probability N1/N. An umpire serves a random pair of two
  distinct players (sampling without replacement). Player part SUPPORTED by SI p.2 (a single
  neutral dissident "does exactly as well as the residents", which requires self-exclusion);
  umpire pair sampling STILL RECONSTRUCTED (no consequence at pure states or for large M).
- A4. Exploration switches to one of the other strategies uniformly (3 for players, 1 for umpires).
  VERIFIED (SI p.2: "to one of the three alternative strategies"; umpires switch "to the
  alternative strategy at random (i.e., without considering a role model)").

## 9. Rare-exploration limit (Methods p.13281)

- Assumes h > 0, hard imitation, exploration rare enough that each mutant is fixed or lost
  before the next.
- Absorbing states (10): honest umpires: 1 allOC, 2 allPC, 3 allOD, 4 allPD, 5 OD+PD;
  corrupt umpires: 6 allOC, 7 allPC, 8 allOD, 9 allPD, 10 OD+PC. Matches CLAUDE.md "10".
- mu is the probability per time step of an exploration step in the player population
  ("mu is the M-fold of the individual exploration rate"); nu = lambda mu in the umpire population.
- Printed transition matrix T (rows = from, columns = to; * = 1 - row sum):
```
row 1:  *     0     0 0 0     lm/N  0     0     0     0
row 2:  m/3   *     0 0 0     0     0     0     0     0
row 3:  m/3   m/3   * 0 m/3   0     0     0     0     0
row 4:  m/3   m/6   0 * m/3   0     0     0     lm    0
row 5:  m/3   0     0 0 *     0     0     lm    0     0
row 6:  lm/N  0     0 0 0     *     0     m/3   m/3   0
row 7:  0     lm    0 0 0     m/3   *     0     0     m/3
row 8:  0     0     0 0 0     0     0     *     0     m/3
row 9:  0     0     0 0 0     0     m/3   m/3   *     0
row 10: 0     lm    0 0 0     0     0     0     0     *
```
  (m = mu, lm = lambda mu)
- Stationary distribution (up to normalization): (N(7+12L)/(3L(2+3L)) + 2, (7+12L)/(2+3L),
  0, 0, 0, 2, 1/(2+3L), 3, 1, (7+9L)/(3L(2+3L))), L = lambda.
- H:C ratio (7+12L)N + 33L + 54L^2 : 7 + 48L + 54L^2. At L = 1: (1/15)(19N+30, 57, 0, 0, 0, 30,
  3, 45, 15, 16), H:C = 19N + 87 : 109 (= 2.541 for N = 10).
- B3 simulated value: "time-averaged ratio of honest-to-corrupt umpires is 2.15" (Fig. 1 caption).

Derivation (U2, VERIFIED from SI p.2-3; implemented in src/rare_exploration.py):
- Advantageous mutants fix with probability 1. Neutral umpire mutants fix with probability 1/N.
  A player mutant that is neutral as a single dissident fixes with probability 1/2 if two
  mutants already do better (entry mu/6), cannot fix if two do worse, and fixes with probability
  1/M if it is neutral throughout (only for h = 0, entry mu/(3M), SI p.3).
- DISCREPANCY D4 (confirmed): row 3 (allOD, honest) omits the transition to 8, although the SI
  text says corrupt umpires invade (allOD, allH) (SI p.2). State 3 is transient, so the
  stationary distribution is unchanged.
- D5 WITHDRAWN: the entry m/6 in row 4 is explained by the SI (p.2); the 0 in row 7 (PD into allPC
  under corrupt umpires) follows from the same rule because two PD players do worse.
- Cost-free information (h = 0, SI p.3): 8 absorbing states; H:C = 14 + 8N + 12M : 25 at
  lambda = 1. Reproduced exactly by our derivation (tests).

## 10. Parameters (base)

| Symbol | Value | Source |
|---|---|---|
| b | 1 | Fig. 1 caption |
| c | 0.5 | Fig. 1 caption |
| f | 0.2 | Fig. 1 caption |
| B | 0.2 | Fig. 1 caption |
| h | 0.1 | Fig. 1 caption |
| A | 2 (0.7 in Fig. 3B) | Fig. 1, Fig. 3 captions |
| M, N, mu, nu, s (small) | 50, 10, 0.001, 0.005, 10^10 | Fig. 1 caption (A, B) |
| M, N, mu, nu, s (large) | 5000, 1000, 0.01, 0.05, 0.3 | Fig. 1 caption (C, D) |
| mu = nu (ODE) | 0.0001, 0.02, 0.07 | Fig. 3 caption |
| ODE initial state | y1 = 1, x = (0.1, 0.4, 0.4, 0.1) | Fig. 3 caption |

## 11. Extension (ASSUMPTION: author's design, CLAUDE.md Section 6; not in Lee et al.)

Mean field (continuous rotation): dy1/dt = [base] + rho (p_new - y1).
- V0: p_new = p0.
- V1: p_new = (1 - kappa) p0 + kappa y1. Then rho (p_new - y1) = rho (1 - kappa)(p0 - y1) exactly
  (derived in sympy, src/rotation.py tests).
- V2: p_new = (1 - kappa) p0 + kappa g(y1), g(y) = y^k / (y^k + (1 - y)^k), k = 2.
- V3: p_new(t) = (1 - kappa) p0 + kappa y1(t - T_lag); default T_lag = 1/rho (mean term length)
  for continuous rotation and T_lag = T for pulses (DECISIONS.md D-010).
Pulse rotation: every T time units a fraction tau of umpires is replaced; mean-field map
y1 -> (1 - tau) y1 + tau p_new. Average rotation rate rho = tau / T.
IBM rotation: each umpire is replaced at rate rho per generation (continuous), or round(tau N)
random umpires are replaced every T generations (pulse); each newcomer is honest with probability
p_new evaluated from the current (or lagged) honest fraction.

## 12. SI figures used for checks (SI_EXTRACT.md)
- SI Fig. 7 (p.7): individual-based runs at mu in {1e-3, 1e-6}, s in {1e10, 10}, nu = mu M / N,
  M = 50, N = 10. Time axes start at 1.4 x 10^8.
- SI Fig. 8 (p.8): individual-based runs at M in {3000, 2000, 1000}, N = M / 5, s in {10, 1, 0.3},
  mu = 0.01, nu = 0.05, 5 x 10^6 time units. Cycle counts digitized by experiments/digitize_si.py
  and compared with our model (supports A1).
- SI Fig. 9 (p.9): mean-field cycle amplitude, period and payoffs over h (0-0.35) and
  mu = nu (0-0.08). Period labels compared with our replicator-mutator periods; supports D6.
  DISCREPANCY D7: the panel axis labels are swapped relative to the caption (the caption is
  correct).
