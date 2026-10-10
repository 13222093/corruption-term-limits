"""Rare-exploration limit: Markov chain over the absorbing states of the imitation process.

Source: Lee et al. (2019), Methods p.13281 ("Rare-Exploration Limit"): hard imitation, h > 0,
ten absorbing states (1-5 honest umpires: allOC, allPC, allOD, allPD, OD+PD; 6-10 corrupt umpires:
allOC, allPC, allOD, allPD, OD+PC), printed transition matrix T and its stationary distribution.

We (a) encode the printed T, and (b) derive T independently from the payoffs by invasion analysis
(SPEC U2; the SI derivation was not available):
- A player mutant (rate mu/3 per mutant type) invades if its payoff exceeds the resident payoff
  in the infinite-population limit. It then fixes with probability 1 (hard imitation), and the
  destination is found by integrating the replicator dynamics of the player population with the
  umpire type held fixed. A neutral player mutant fixes with probability 1/M (0 in the paper's
  M -> infinity convention).
- An umpire mutant (rate lambda mu) fixes with probability 1 if it earns more, 1/N if it earns the
  same, 0 otherwise. After fixation the player population moves to the attractor of the
  replicator dynamics under the new umpire type.
"""
from __future__ import annotations

import numpy as np
import sympy as sp
from scipy.integrate import solve_ivp

from .params import Params
from .payoffs import Q_C, Q_H, umpire_payoffs

STATE_NAMES = ["H:allOC", "H:allPC", "H:allOD", "H:allPD", "H:OD+PD",
               "C:allOC", "C:allPC", "C:allOD", "C:allPD", "C:OD+PC"]


def absorbing_states(p: Params):
    """Return list of (x, honest) for states 1..10 (Fig. 2 caption, Methods p.13281)."""
    e = np.eye(4)
    fp5 = np.array([0, 0, p.h / (p.f + p.A), (p.f + p.A - p.h) / (p.f + p.A)])
    fp10 = np.array([0, (p.f + p.B - p.h) / (p.f + p.B), p.h / (p.f + p.B), 0])
    return ([(e[i], True) for i in range(4)] + [(fp5, True)]
            + [(e[i], False) for i in range(4)] + [(fp10, False)])


def printed_T(mu, lam, N):
    """Transition matrix as printed (Methods p.13281). Works with floats or sympy symbols."""
    m, lm = mu, lam * mu
    T = [[0, 0, 0, 0, 0, lm / N, 0, 0, 0, 0],
         [m / 3, 0, 0, 0, 0, 0, 0, 0, 0, 0],
         [m / 3, m / 3, 0, 0, m / 3, 0, 0, 0, 0, 0],
         [m / 3, m / 6, 0, 0, m / 3, 0, 0, 0, lm, 0],
         [m / 3, 0, 0, 0, 0, 0, 0, lm, 0, 0],
         [lm / N, 0, 0, 0, 0, 0, 0, m / 3, m / 3, 0],
         [0, lm, 0, 0, 0, m / 3, 0, 0, 0, m / 3],
         [0, 0, 0, 0, 0, 0, 0, 0, 0, m / 3],
         [0, 0, 0, 0, 0, 0, m / 3, m / 3, 0, 0],
         [0, lm, 0, 0, 0, 0, 0, 0, 0, 0]]
    if isinstance(mu, sp.Basic) or isinstance(lam, sp.Basic) or isinstance(N, sp.Basic):
        Ts = sp.Matrix(T)
        for i in range(10):
            Ts[i, i] = 1 - sum(Ts[i, j] for j in range(10) if j != i)
        return Ts
    T = np.array(T, dtype=float)
    np.fill_diagonal(T, 1.0 - T.sum(axis=1))
    return T


def _player_attractor(p: Params, x0, honest: bool, T_int: float = 1e6):
    """Integrate replicator dynamics of players (no exploration) with fixed umpire type.

    Long horizon because some approaches are algebraic (zero transversal eigenvalue, the open
    arrowheads of Fig. 2), e.g. PC invading allPD under corrupt umpires: x4 ~ 1/((f+B) t).
    """
    Q = Q_H(p) if honest else Q_C(p)

    def rhs(t, x):
        S = x.sum()
        xh = x / S
        fit = Q @ xh
        return x * (fit - xh @ fit)

    sol = solve_ivp(rhs, (0, T_int), np.asarray(x0, float), method="LSODA", rtol=1e-10,
                    atol=1e-13)
    x = sol.y[:, -1]
    return x / x.sum()


def _classify(p: Params, x, honest: bool, tol: float = 1e-3) -> int:
    states = absorbing_states(p)
    best, dist = -1, np.inf
    for k, (xs, hs) in enumerate(states):
        if hs != honest:
            continue
        d = np.abs(xs - x).sum()
        if d < dist:
            best, dist = k, d
    if dist > tol:
        raise RuntimeError(f"endpoint {x} not near an absorbing state (dist {dist})")
    return best


def derive_transitions(p: Params, eps: float = 1e-4, tie_tol: float = 1e-12):
    """Derive transition events from each absorbing state by invasion analysis.

    Returns a list of dicts: {from, to, kind ('player'/'umpire'), mutant, outcome
    ('advantageous'/'neutral')}. Disadvantageous mutants are omitted.
    """
    states = absorbing_states(p)
    events = []
    for k, (x, honest) in enumerate(states):
        Q = Q_H(p) if honest else Q_C(p)
        fit = Q @ x
        resident_payoff = x @ fit
        present = x > 1e-12
        for j in range(4):
            if present[j]:
                continue
            adv = fit[j] - resident_payoff
            if adv < -tie_tol:
                continue
            if adv > tie_tol:
                x0 = (1 - eps) * x
                x0[j] += eps
                dest = _classify(p, _player_attractor(p, x0, honest), honest)
                events.append(dict(frm=k, to=dest, kind="player", mutant=j,
                                   outcome="advantageous"))
            else:
                # neutral mutant: if it fixes by drift the population becomes pure j
                xj = np.zeros(4)
                xj[j] = 1.0
                dest = _classify(p, xj, honest) if np.all(present == (x > 1 - 1e-12)) else None
                if dest is not None:
                    events.append(dict(frm=k, to=dest, kind="player", mutant=j,
                                       outcome="neutral"))
        PH, PCr = umpire_payoffs(p, x)
        adv = (PCr - PH) if honest else (PH - PCr)
        if adv < -tie_tol:
            continue
        new_honest = not honest
        if adv > tie_tol:
            # Absent player types stay absent (no exploration between events); a pure state
            # stays put, a mixed state moves under the new umpire type.
            dest = _classify(p, _player_attractor(p, x, new_honest), new_honest)
            events.append(dict(frm=k, to=dest, kind="umpire", mutant=int(not new_honest),
                               outcome="advantageous"))
        else:
            dest = _classify(p, x, new_honest)
            events.append(dict(frm=k, to=dest, kind="umpire", mutant=int(not new_honest),
                               outcome="neutral"))
    return events


def derived_T(p: Params, mu, lam, N, M=None):
    """Transition matrix from derive_transitions. M=None uses the paper's convention that
    neutral player mutants never fix (M -> infinity); otherwise they fix with probability 1/M."""
    events = derive_transitions(p)
    symbolic = any(isinstance(v, sp.Basic) for v in (mu, lam, N)) or isinstance(M, sp.Basic)
    T = sp.zeros(10, 10) if symbolic else np.zeros((10, 10))
    for ev in events:
        if ev["kind"] == "player":
            rate = mu / 3
            prob = 1 if ev["outcome"] == "advantageous" else (0 if M is None else 1 / M)
        else:
            rate = lam * mu
            prob = 1 if ev["outcome"] == "advantageous" else 1 / N
        T[ev["frm"], ev["to"]] += rate * prob
    for i in range(10):
        T[i, i] = 1 - sum(T[i, j] for j in range(10) if j != i)
    return T


def stationary(T) -> np.ndarray:
    """Stationary distribution (left eigenvector for eigenvalue 1) of a numeric T."""
    T = np.asarray(T, dtype=float)
    A = T.T - np.eye(T.shape[0])
    A[-1, :] = 1.0
    b = np.zeros(T.shape[0])
    b[-1] = 1.0
    return np.linalg.lstsq(A, b, rcond=None)[0]


def stationary_symbolic(T: sp.Matrix) -> sp.Matrix:
    n = T.shape[0]
    pi = sp.symbols(f"pi0:{n}")
    eqs = [sum(pi[i] * T[i, j] for i in range(n)) - pi[j] for j in range(n - 1)]
    eqs.append(sum(pi) - 1)
    sol = sp.solve(eqs, pi, dict=True)[0]
    return sp.Matrix([sp.simplify(sol[s]) for s in pi])


def paper_stationary(lam, N):
    """Stationary vector printed in Methods p.13281 (unnormalized)."""
    L = lam
    return [N * (7 + 12 * L) / (3 * L * (2 + 3 * L)) + 2, (7 + 12 * L) / (2 + 3 * L), 0, 0, 0,
            2, 1 / (2 + 3 * L), 3, 1, (7 + 9 * L) / (3 * L * (2 + 3 * L))]


def hc_ratio(pi) -> float:
    pi = np.asarray(pi, dtype=float)
    return pi[:5].sum() / pi[5:].sum()


def expected_cycle_time(T, mu_scale: float = 1.0) -> dict:
    """Mean residence time in each state (in units of exploration attempts / mu)."""
    T = np.asarray(T, dtype=float)
    out = {}
    for i in range(10):
        leave = 1.0 - T[i, i]
        out[STATE_NAMES[i]] = np.inf if leave == 0 else 1.0 / leave
    return out
