"""Diagnostic variants of the base individual-based model (no rotation), used only to
investigate the remaining gap in benchmark B3 (CHANGES_SI.md). Each switch replaces one choice
that the SI of Lee et al. (2019) leaves open by a plausible alternative. With all switches off
the kernel reproduces src.ibm.simulate exactly (same random-number sequence; tested).

Switches:
- explore_any: an exploring individual draws a strategy uniformly from all strategies,
  including its own (so only 3/4 of player and 1/2 of umpire exploration events change
  anything), instead of one of the other strategies.
- role_any: the role model is drawn from the whole population, including the focal itself.
- self_payoff: payoffs are evaluated with replacement (a player may meet itself; an umpire's
  two players are drawn independently), i.e. the infinite-population formulas at x = counts/M.
- pair_step: each elementary step updates one random player and one random umpire, instead of
  one individual drawn from all M + N (per-capita update rates then differ between populations).
"""
from __future__ import annotations

import math

import numpy as np
from numba import njit

from .ibm import _pick, fermi, player_payoff, umpire_payoffs
from .params import Params
from .payoffs import Q_C, Q_H


@njit(cache=True)
def _player_payoff_self(i, cnt, M, y, QH, QC):
    acc = 0.0
    for k in range(4):
        acc += (y * QH[i, k] + (1.0 - y) * QC[i, k]) * cnt[k]
    return acc / M


@njit(cache=True)
def _umpire_payoffs_self(cnt, M, f, B):
    x2 = cnt[1] / M
    x3 = cnt[2] / M
    x4 = cnt[3] / M
    PH = 2.0 * f * (1.0 - x4) ** 2
    PC = 2.0 * f * (1.0 - x2) ** 2 + 2.0 * B * (x3 + x4) * (1.0 - x2)
    return PH, PC


@njit(cache=True)
def _player_update(cnt, Mf, y, mu, s, QH, QC, explore_any, role_any, self_payoff):
    i = _pick(cnt, Mf, -1)
    if np.random.random() < mu:
        if explore_any:
            j = int(np.random.random() * 4.0)
        else:
            j = int(np.random.random() * 3.0)
            if j >= i:
                j += 1
        if j != i:
            cnt[i] -= 1
            cnt[j] += 1
        return
    if role_any:
        j = _pick(cnt, Mf, -1)
    else:
        j = _pick(cnt, Mf - 1.0, i)
    if j != i:
        if self_payoff:
            Pi = _player_payoff_self(i, cnt, Mf, y, QH, QC)
            Pj = _player_payoff_self(j, cnt, Mf, y, QH, QC)
        else:
            Pi = player_payoff(i, cnt, Mf, y, QH, QC)
            Pj = player_payoff(j, cnt, Mf, y, QH, QC)
        if np.random.random() < fermi(Pi - Pj, s):
            cnt[i] -= 1
            cnt[j] += 1


@njit(cache=True)
def _umpire_update(n1, cnt, Mf, Nf, nu, s, f, B, explore_any, role_any, self_payoff):
    honest = np.random.random() * Nf < n1
    if np.random.random() < nu:
        if explore_any:
            new_honest = np.random.random() < 0.5
            if new_honest != honest:
                n1 += 1 if new_honest else -1
        else:
            n1 += -1 if honest else 1
        return n1
    if role_any:
        rm_honest = np.random.random() * Nf < n1
    else:
        n_h_other = n1 - (1 if honest else 0)
        rm_honest = np.random.random() * (Nf - 1.0) < n_h_other
    if rm_honest != honest:
        if self_payoff:
            PH, PC = _umpire_payoffs_self(cnt, Mf, f, B)
        else:
            PH, PC = umpire_payoffs(cnt, Mf, f, B)
        if honest:
            if np.random.random() < fermi(PH - PC, s):
                n1 -= 1
        else:
            if np.random.random() < fermi(PC - PH, s):
                n1 += 1
    return n1


@njit(cache=True)
def simulate_diag(QH, QC, f, B, M, N, mu, nu, s, cnt0, n1_0, t_end, rec_dt, seed,
                  explore_any, role_any, self_payoff, pair_step):
    """Base model (no rotation). Time in generations as in src.ibm.simulate; with pair_step,
    one step (one player and one umpire update) advances time by 1/M generations."""
    np.random.seed(seed)
    cnt = cnt0.copy()
    n1 = n1_0
    Mf = float(M)
    Nf = float(N)
    R = Mf + Nf
    dt = 1.0 / Mf if pair_step else 1.0 / R
    n_rec = int(t_end / rec_dt) + 1
    times = np.empty(n_rec)
    rc = np.empty((n_rec, 4), dtype=np.int64)
    rn = np.empty(n_rec, dtype=np.int64)
    t = 0.0
    k_rec = 0
    next_rec = 0.0
    while True:
        while k_rec < n_rec and t >= next_rec:
            times[k_rec] = next_rec
            for q in range(4):
                rc[k_rec, q] = cnt[q]
            rn[k_rec] = n1
            k_rec += 1
            next_rec = k_rec * rec_dt
        if k_rec >= n_rec:
            break
        if pair_step:
            y = n1 / Nf
            _player_update(cnt, Mf, y, mu, s, QH, QC, explore_any, role_any, self_payoff)
            n1 = _umpire_update(n1, cnt, Mf, Nf, nu, s, f, B, explore_any, role_any,
                                self_payoff)
        else:
            u = np.random.random() * R
            y = n1 / Nf
            if u < Mf:
                _player_update(cnt, Mf, y, mu, s, QH, QC, explore_any, role_any, self_payoff)
            else:
                n1 = _umpire_update(n1, cnt, Mf, Nf, nu, s, f, B, explore_any, role_any,
                                    self_payoff)
        t += dt
    return times, rc, rn


def run_diag(p: Params, M: int, N: int, s: float, t_end: float, rec_dt: float, seed: int,
             x0=None, y0: float = 1.0, explore_any: bool = False, role_any: bool = False,
             self_payoff: bool = False, pair_step: bool = False) -> dict:
    if x0 is None:
        x0 = np.array([0.0, 0.0, 1.0, 0.0])
    x0 = np.asarray(x0, dtype=float)
    cnt0 = np.floor(x0 * M).astype(np.int64)
    rem = M - cnt0.sum()
    order = np.argsort(-(x0 * M - cnt0))
    for k in range(rem):
        cnt0[order[k % 4]] += 1
    n1_0 = int(round(y0 * N))
    times, rc, rn = simulate_diag(
        np.ascontiguousarray(Q_H(p)), np.ascontiguousarray(Q_C(p)), p.f, p.B, int(M), int(N),
        p.mu, p.nu, float(s), cnt0, n1_0, float(t_end), float(rec_dt), int(seed),
        bool(explore_any), bool(role_any), bool(self_payoff), bool(pair_step))
    return {"t": times, "x": rc / float(M), "y": rn / float(N), "counts": rc, "n_honest": rn}
