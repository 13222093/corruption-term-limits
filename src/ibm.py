"""Individual-based model (IBM) of players and umpires with Fermi imitation and exploration.

Main-text sources (Lee et al. 2019, PNAS 116:13276):
- Imitation probability Pr(X -> Y) = 1 / (1 + exp(s (P_X - P_Y))): Methods p.13280 ("Dynamics").
- Exploration with probability mu (players) or nu (umpires) to another strategy: p.13277, p.13280.
- Average payoffs as functions of the counts M1..M4, N1, N2: p.13277 right column.

ASSUMPTIONS (SI not available, SPEC U1; DECISIONS D-003 to D-007, D-011):
- Asynchronous random sequential updating; one event = one individual (uniform over all M + N)
  revises its strategy. Rotation (extension) adds replacement events at rate rho per umpire.
- Role model drawn uniformly from the other members of the focal's population.
- Expected payoffs from current counts; co-player excluded from own count; umpires serve pairs of
  distinct players.
Because individuals of a type are exchangeable and payoffs depend only on counts, the simulation
tracks counts only; this is exact for the process described above.

Time is reported in generations: one generation = (M + N + rho N) events, i.e. each individual
revises on average once per generation. Elementary steps (Fig. 1 axes) = generations * (M + N)
when rho = 0.
"""
from __future__ import annotations

import math

import numpy as np
from numba import njit

from .params import Params
from .payoffs import Q_C, Q_H

ROT_OFF, ROT_CONT, ROT_PULSE = 0, 1, 2
V0, V1, V2, V3 = 0, 1, 2, 3
IBM_VARIANTS = ("si", "reconstructed")


@njit(cache=True)
def fermi(d, s):
    """Probability that X imitates Y, d = P_X - P_Y (numerically stable; ties give 1/2)."""
    a = s * d
    if a > 0.0:
        e = math.exp(-a) if a < 745.0 else 0.0
        return e / (1.0 + e)
    e = math.exp(a) if a > -745.0 else 0.0
    return 1.0 / (1.0 + e)


@njit(cache=True)
def player_payoff(i, cnt, M, y, QH, QC):
    """Expected payoff of a type-i player; co-player drawn from the other M - 1 players."""
    acc = 0.0
    for k in range(4):
        m = cnt[k] - (1 if k == i else 0)
        acc += (y * QH[i, k] + (1.0 - y) * QC[i, k]) * m
    return acc / (M - 1.0)


@njit(cache=True)
def umpire_payoffs(cnt, M, f, B):
    """Expected (P_H, P_C) for an umpire serving two distinct random players."""
    pair = M * (M - 1.0)
    no_pd = (M - cnt[3]) * (M - cnt[3] - 1.0) / pair
    no_pc = (M - cnt[1]) * (M - cnt[1] - 1.0) / pair
    nd = cnt[2] + cnt[3]
    d_no_pc = 2.0 * nd * (M - cnt[1] - 1.0) / pair
    return 2.0 * f * no_pd, 2.0 * f * no_pc + B * d_no_pc


@njit(cache=True)
def _pick(cnt, total, skip):
    """Draw a type with probability proportional to cnt, after removing one individual of type
    `skip` (skip = -1 removes nobody)."""
    r = np.random.random() * total
    acc = 0.0
    for k in range(cnt.shape[0]):
        acc += cnt[k] - (1 if k == skip else 0)
        if r < acc:
            return k
    return cnt.shape[0] - 1


@njit(cache=True)
def _conformist(y, k):
    if y <= 0.0:
        return 0.0
    if y >= 1.0:
        return 1.0
    a = y ** k
    return a / (a + (1.0 - y) ** k)


@njit(cache=True)
def _p_new(variant, y, ylag, p0, kappa, kexp):
    if variant == 0:
        return p0
    if variant == 1:
        return (1.0 - kappa) * p0 + kappa * y
    if variant == 2:
        return (1.0 - kappa) * p0 + kappa * _conformist(y, kexp)
    return (1.0 - kappa) * p0 + kappa * ylag


@njit(cache=True)
def simulate(QH, QC, f, B, M, N, mu, nu, s, cnt0, n1_0, t_end, rec_dt, seed,
             rot_mode, rho, variant, p0, kappa, kexp, T_lag, pulse_T, pulse_tau, hist_dt):
    """Run the IBM for t_end generations, recording the state every rec_dt generations.

    Returns (times, counts[n_rec, 4], n_honest[n_rec], n_events).
    """
    np.random.seed(seed)
    cnt = cnt0.copy()
    n1 = n1_0
    Mf = float(M)
    Nf = float(N)
    rate_rot = rho * Nf if rot_mode == ROT_CONT else 0.0
    R = Mf + Nf + rate_rot
    dt = 1.0 / R
    n_rec = int(t_end / rec_dt) + 1
    times = np.empty(n_rec)
    rc = np.empty((n_rec, 4), dtype=np.int64)
    rn = np.empty(n_rec, dtype=np.int64)
    # history of y for delayed inheritance (V3)
    use_hist = variant == 3 and rot_mode != ROT_OFF
    L = int(T_lag / hist_dt) + 3 if use_hist else 1
    hist = np.empty(L)
    y_init = n1_0 / Nf
    k_hist = 0
    next_hist = 0.0
    next_pulse = pulse_T
    t = 0.0
    k_rec = 0
    next_rec = 0.0
    n_events = 0
    while True:
        if use_hist:
            while t >= next_hist:
                hist[k_hist % L] = n1 / Nf
                k_hist += 1
                next_hist = k_hist * hist_dt
        ylag = y_init
        if use_hist and t - T_lag >= 0.0:
            kl = int((t - T_lag) / hist_dt)
            if kl > k_hist - 1:
                kl = k_hist - 1
            ylag = hist[kl % L]
        # pulse rotation: replace round(tau N) random umpires every pulse_T generations
        if rot_mode == ROT_PULSE and t >= next_pulse:
            n_rep = int(round(pulse_tau * Nf))
            y_now = n1 / Nf
            pn = _p_new(variant, y_now, ylag, p0, kappa, kexp)
            # leaving umpires: sampled without replacement
            h_left = n1
            tot_left = N
            for _ in range(n_rep):
                if np.random.random() * tot_left < h_left:
                    h_left -= 1
                tot_left -= 1
            new_h = 0
            for _ in range(n_rep):
                if np.random.random() < pn:
                    new_h += 1
            n1 = h_left + new_h
            next_pulse += pulse_T
        # record after any pulse at this time (same convention as the mean-field pulse map)
        while k_rec < n_rec and t >= next_rec:
            times[k_rec] = next_rec
            for q in range(4):
                rc[k_rec, q] = cnt[q]
            rn[k_rec] = n1
            k_rec += 1
            next_rec = k_rec * rec_dt
        if k_rec >= n_rec:
            break
        u = np.random.random() * R
        y = n1 / Nf
        if u < Mf:
            # player event
            i = _pick(cnt, Mf, -1)
            if np.random.random() < mu:
                j = int(np.random.random() * 3.0)
                if j >= i:
                    j += 1
                cnt[i] -= 1
                cnt[j] += 1
            else:
                j = _pick(cnt, Mf - 1.0, i)
                if j != i:
                    Pi = player_payoff(i, cnt, Mf, y, QH, QC)
                    Pj = player_payoff(j, cnt, Mf, y, QH, QC)
                    if np.random.random() < fermi(Pi - Pj, s):
                        cnt[i] -= 1
                        cnt[j] += 1
        elif u < Mf + Nf:
            # umpire event; focal honest with probability n1 / N
            honest = np.random.random() * Nf < n1
            if np.random.random() < nu:
                n1 += -1 if honest else 1
            else:
                # role model from the other N - 1 umpires
                n_h_other = n1 - (1 if honest else 0)
                rm_honest = np.random.random() * (Nf - 1.0) < n_h_other
                if rm_honest != honest:
                    PH, PC = umpire_payoffs(cnt, Mf, f, B)
                    if honest:
                        if np.random.random() < fermi(PH - PC, s):
                            n1 -= 1
                    else:
                        if np.random.random() < fermi(PC - PH, s):
                            n1 += 1
        else:
            # continuous rotation: a random umpire is replaced by a newcomer
            pn = _p_new(variant, y, ylag, p0, kappa, kexp)
            leaving_honest = np.random.random() * Nf < n1
            new_honest = np.random.random() < pn
            n1 += (1 if new_honest else 0) - (1 if leaving_honest else 0)
        t += dt
        n_events += 1
    return times, rc, rn, n_events


def run_ibm(p: Params, M: int, N: int, s: float, t_end: float, rec_dt: float, seed: int,
            x0=None, y0: float = 1.0, rot_mode: int = ROT_OFF, rho: float = 0.0,
            variant: int = V0, p0: float = 1.0, kappa: float = 0.0, kexp: float = 2.0,
            T_lag: float = 0.0, pulse_T: float = 1.0, pulse_tau: float = 0.0,
            hist_dt: float | None = None, ibm_variant: str = "si") -> dict:
    """Python wrapper. x0: initial player frequencies (default all OD as in Fig. 1C); y0 honest
    fraction (default 1, Fig. 1D starts with honest umpires).

    ibm_variant: "si" (default) or "reconstructed". The SI of Lee et al. (2019) does not state
    the update order, the time unit or how finite-population payoffs are evaluated; every rule it
    does state (exploration to one of the other strategies without a role model, nu = mu M / N,
    ties imitated with probability 1/2, a single neutral dissident doing exactly as well as the
    residents, neutral umpire fixation 1/N) is already satisfied by the pre-SI reconstruction
    (SI_EXTRACT.md). The two variants therefore run the same kernel and give identical output
    for the same seed (tests/test_si_rules.py); the switch is kept so that a future difference
    (for example the authors' code) can be compared directly. DECISIONS.md D-017.
    """
    if ibm_variant not in IBM_VARIANTS:
        raise ValueError(f"unknown ibm_variant {ibm_variant!r}; choose from {IBM_VARIANTS}")
    if x0 is None:
        x0 = np.array([0.0, 0.0, 1.0, 0.0])
    x0 = np.asarray(x0, dtype=float)
    cnt0 = np.floor(x0 * M).astype(np.int64)
    rem = M - cnt0.sum()
    order = np.argsort(-(x0 * M - cnt0))
    for k in range(rem):
        cnt0[order[k % 4]] += 1
    n1_0 = int(round(y0 * N))
    if hist_dt is None:
        hist_dt = max(T_lag / 200.0, 0.01) if T_lag > 0 else 1.0
    times, rc, rn, n_ev = simulate(
        np.ascontiguousarray(Q_H(p)), np.ascontiguousarray(Q_C(p)), p.f, p.B, int(M), int(N),
        p.mu, p.nu, float(s), cnt0, n1_0, float(t_end), float(rec_dt), int(seed),
        int(rot_mode), float(rho), int(variant), float(p0), float(kappa), float(kexp),
        float(T_lag), float(pulse_T), float(pulse_tau), float(hist_dt))
    return {"t": times, "x": rc / float(M), "y": rn / float(N), "counts": rc, "n_honest": rn,
            "n_events": int(n_ev), "M": M, "N": N}
