"""Payoffs of players and umpires in the corruption game of Lee et al. (2019).

Sources (PNAS 116:13276):
- Game rules: p.13277, right column ("To sum up, ...").
- Payoff matrices Q_H, Q_C: Methods p.13280, right column ("Payoffs").
- Umpire income rules: Methods p.13280, right column.
- P_H - P_C closed form: Methods p.13281, left column ("Large-Population Limit").
- Q(y) weighting: printed as y1 Q_C + (1 - y1) Q_H; we use y1 Q_H + (1 - y1) Q_C
  (SPEC D1, DECISIONS D-001).
"""
from __future__ import annotations

import numpy as np

from .params import OC, PC, OD, PD, H, C, Params

COOPERATORS = (OC, PC)
PRUDENT = (PC, PD)


def Q_H(p: Params) -> np.ndarray:
    """Payoff matrix when the umpire is honest (Methods p.13280)."""
    b, c, f, h, A = p.b, p.c, p.f, p.h, p.A
    return np.array([
        [b - c - f,     b - c - f,     -c - f,     0.0],
        [b - c - f - h, b - c - f - h, -c - f - h, -h],
        [b - f - A,     b - f - A,     -f - A,     0.0],
        [-h,            -h,            -h,         -h],
    ])


def Q_C(p: Params) -> np.ndarray:
    """Payoff matrix when the umpire is corrupt (Methods p.13280)."""
    b, c, f, h, B = p.b, p.c, p.f, p.h, p.B
    return np.array([
        [b - c - f,         0.0, -c - f,         -c - f],
        [-h,                -h,  -h,             -h],
        [b - f - B,         0.0, -f - B,         -f - B],
        [b - f - B - h,     -h,  -f - B - h,     -f - B - h],
    ])


def Q_y(p: Params, y: float) -> np.ndarray:
    """Average player payoff matrix for honest fraction y (DECISIONS D-001)."""
    return y * Q_H(p) + (1.0 - y) * Q_C(p)


def Q_y_printed(p: Params, y: float) -> np.ndarray:
    """The weighting as printed in the PDF (Methods p.13281). Kept only to test D-001."""
    return y * Q_C(p) + (1.0 - y) * Q_H(p)


def player_payoffs(p: Params, x: np.ndarray, y: float) -> np.ndarray:
    """Expected payoff of each player strategy in an infinite population."""
    return Q_y(p, y) @ np.asarray(x, dtype=float)


def umpire_payoffs(p: Params, x: np.ndarray) -> tuple[float, float]:
    """Expected incomes (P_H, P_C) of an umpire serving a random pair (infinite population).

    Derived from the income rules (Methods p.13280):
    P_H = 2f (1 - x4)^2;  P_C = 2f (1 - x2)^2 + 2B (x3 + x4)(1 - x2).
    """
    x = np.asarray(x, dtype=float)
    PH = 2 * p.f * (1 - x[PD]) ** 2
    PCr = 2 * p.f * (1 - x[PC]) ** 2 + 2 * p.B * (x[OD] + x[PD]) * (1 - x[PC])
    return PH, PCr


def umpire_diff_paper(p: Params, x: np.ndarray) -> float:
    """P_H - P_C exactly as printed (Methods p.13281)."""
    x1, x2, x3, x4 = np.asarray(x, dtype=float)
    return 2 * p.f * (x2 - x4) * (1 + x1 + x3) - 2 * p.B * (x3 + x4) * (1 - x2)


# ---------------------------------------------------------------------------
# Rule-based reference implementation of a single game (p.13277). Used to
# cross-check the matrices and the umpire income by brute-force enumeration.
# ---------------------------------------------------------------------------

def play_game(p: Params, s1: int, s2: int, umpire: int) -> tuple[float, float, float]:
    """Return (payoff of player 1, payoff of player 2, umpire income) for one game.

    Rules (p.13277 right column): prudent players pay h and learn the umpire type; a PD who
    learns the umpire is honest drops out, and so does a PC who learns the umpire is corrupt.
    If both proceed, both pay f; with a corrupt umpire each defector also pays B. The donation
    game is then played; with an honest umpire each defector pays the fine A (not umpire income).
    """
    pay = [0.0, 0.0]
    strategies = (s1, s2)
    proceeds = [True, True]
    for i, s in enumerate(strategies):
        if s in PRUDENT:
            pay[i] -= p.h
            if s == PD and umpire == H:
                proceeds[i] = False
            if s == PC and umpire == C:
                proceeds[i] = False
    if not all(proceeds):
        return pay[0], pay[1], 0.0
    income = 0.0
    for i, s in enumerate(strategies):
        pay[i] -= p.f
        income += p.f
        if s not in COOPERATORS and umpire == C:
            pay[i] -= p.B
            income += p.B
    for i, s in enumerate(strategies):
        other = 1 - i
        if s in COOPERATORS:
            pay[i] -= p.c
            pay[other] += p.b
        elif umpire == H:
            pay[i] -= p.A
    return pay[0], pay[1], income


# ---------------------------------------------------------------------------
# Finite-population expected payoffs (ASSUMPTION, DECISIONS D-005).
# ---------------------------------------------------------------------------

def player_payoffs_finite(p: Params, counts: np.ndarray, n_honest: int, N: int) -> np.ndarray:
    """Expected payoff of a focal player of each type; co-player drawn from the other M - 1."""
    counts = np.asarray(counts, dtype=float)
    M = counts.sum()
    Q = Q_y(p, n_honest / N)
    out = np.empty(4)
    for i in range(4):
        others = counts.copy()
        others[i] -= 1.0
        out[i] = Q[i] @ others / (M - 1.0)
    return out


def umpire_payoffs_finite(p: Params, counts: np.ndarray) -> tuple[float, float]:
    """Expected income of an honest and a corrupt umpire serving two distinct random players."""
    m = np.asarray(counts, dtype=float)
    M = m.sum()
    pair = M * (M - 1.0)
    no_pd = (M - m[PD]) * (M - m[PD] - 1.0) / pair
    no_pc = (M - m[PC]) * (M - m[PC] - 1.0) / pair
    # E[#defectors * 1{no PC}] = 2 P(first is a defector and second is not PC)
    nd = m[OD] + m[PD]
    d_no_pc = 2.0 * nd * (M - m[PC] - 1.0) / pair
    PH = 2 * p.f * no_pd
    PCr = 2 * p.f * no_pc + p.B * d_no_pc
    return PH, PCr
