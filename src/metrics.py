"""Metrics defined in METRICS.md (pre-registered). Each function cites its metric ID."""
from __future__ import annotations

import numpy as np

from .params import Params
from .payoffs import Q_y

THETA = 0.5  # M5 threshold: majority corrupt


def cooperation(x: np.ndarray) -> np.ndarray:
    """M2: C = x1 + x2."""
    x = np.atleast_2d(x)
    return x[:, 0] + x[:, 1]


def realized_cooperation(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """M2b: expected donations per player per game, accounting for drop-outs."""
    x = np.atleast_2d(x)
    y = np.asarray(y)
    x1, x2, x4 = x[:, 0], x[:, 1], x[:, 3]
    return x1 * (y * (1 - x4) + (1 - y) * (1 - x2)) + x2 * y * (1 - x4)


def mean_payoff(p: Params, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """M2c: W = x . Q(y) x."""
    x = np.atleast_2d(x)
    y = np.asarray(y)
    from .payoffs import Q_C, Q_H
    QH, QC = Q_H(p), Q_C(p)
    wh = np.einsum("ti,ij,tj->t", x, QH, x)
    wc = np.einsum("ti,ij,tj->t", x, QC, x)
    return y * wh + (1 - y) * wc


def episodes(t: np.ndarray, y: np.ndarray, theta: float = THETA, merge_gap: float = 0.0,
             min_dur: float = 0.0):
    """M5: maximal intervals with y < theta. Returns list of (i_start, i_end) index pairs
    (inclusive start, exclusive end) after merging gaps shorter than merge_gap and dropping
    intervals shorter than min_dur. Intervals touching the window edges are kept only if they
    start and end inside the window (censored episodes are dropped)."""
    below = y < theta
    if not below.any():
        return []
    d = np.diff(below.astype(np.int8))
    starts = list(np.where(d == 1)[0] + 1)
    ends = list(np.where(d == -1)[0] + 1)
    if below[0]:
        starts = [0] + starts
    if below[-1]:
        ends = ends + [len(y)]
    iv = list(zip(starts, ends))
    if merge_gap > 0 and iv:
        merged = [list(iv[0])]
        for s, e in iv[1:]:
            if t[s] - t[merged[-1][1] - 1] < merge_gap:
                merged[-1][1] = e
            else:
                merged.append([s, e])
        iv = [tuple(m) for m in merged]
    out = []
    for s, e in iv:
        if s == 0 or e == len(y):
            continue  # censored by the window
        if t[e - 1] - t[s] + (t[1] - t[0]) < min_dur:
            continue
        out.append((s, e))
    return out


def summarize(t: np.ndarray, x: np.ndarray, y: np.ndarray, p: Params, kind: str = "ode",
              theta: float = THETA) -> dict:
    """Compute M1-M8 on a recorded window (already without burn-in).

    kind = 'ode' uses max-min amplitude and the absolute minimum of C; kind = 'ibm' uses
    quantile-based amplitude and the 5th percentile of C, and merges/drops short episodes
    (5 generations), as pre-registered.
    """
    t = np.asarray(t, float)
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    C = cooperation(x)
    R = realized_cooperation(x, y)
    W = mean_payoff(p, x, y)
    T = t[-1] - t[0] + (t[1] - t[0])
    out = {"ybar": y.mean(), "Cbar": C.mean(), "Rbar": R.mean(), "Wbar": W.mean(),
           "x1bar": x[:, 0].mean(), "x2bar": x[:, 1].mean(), "x3bar": x[:, 2].mean(),
           "x4bar": x[:, 3].mean(), "corrupt_majority_time": float(np.mean(y < theta)),
           "y_sd": y.std(), "C_sd": C.std(), "C_absmin": C.min(), "y_absmin": y.min(),
           "y_absmax": y.max()}
    if kind == "ode":
        out["A_y"] = y.max() - y.min()
        out["A_C"] = C.max() - C.min()
        out["C_min"] = C.min()
        ep = episodes(t, y, theta)
    else:
        out["A_y"] = np.quantile(y, 0.95) - np.quantile(y, 0.05)
        out["A_C"] = np.quantile(C, 0.95) - np.quantile(C, 0.05)
        out["C_min"] = np.quantile(C, 0.05)
        ep = episodes(t, y, theta, merge_gap=5.0, min_dur=5.0)
    out["n_episodes"] = len(ep)
    out["episode_freq_per_1000"] = 1000.0 * len(ep) / T
    if ep:
        Dy = [1.0 - y[s:e].min() for s, e in ep]
        DC = [C[s:e].min() for s, e in ep]
        dur = [t[e - 1] - t[s] + (t[1] - t[0]) for s, e in ep]
        out.update(depth_y=float(np.mean(Dy)), depth_C=float(np.mean(DC)),
                   recovery_time=float(np.mean(dur)), depth_y_max=float(np.max(Dy)),
                   depth_C_min=float(np.min(DC)))
    else:
        out.update(depth_y=np.nan, depth_C=np.nan, recovery_time=np.nan, depth_y_max=np.nan,
                   depth_C_min=np.nan)
    return {k: float(v) for k, v in out.items()}


def classify_attractor(t: np.ndarray, y: np.ndarray, amp_tol: float = 1e-6,
                       per_tol: float = 1e-4) -> dict:
    """Mean-field attractor type (METRICS.md Section 2)."""
    amp = float(y.max() - y.min())
    if amp < amp_tol:
        return {"type": "equilibrium", "period": np.nan, "amplitude": amp}
    i = np.where((y[1:-1] > y[:-2]) & (y[1:-1] >= y[2:]))[0] + 1
    if len(i) < 6:
        return {"type": "cycle", "period": np.nan, "amplitude": amp}
    peaks = y[i][-5:]
    periodic = bool(np.max(peaks) - np.min(peaks) < per_tol)
    return {"type": "periodic" if periodic else "cycle",
            "period": float(np.mean(np.diff(t[i][-5:]))), "amplitude": amp}


def bootstrap_ci(values, n_boot: int = 10000, seed: int = 0, level: float = 0.95):
    """Mean and percentile bootstrap CI; ignores NaN. Returns (mean, lo, hi, n)."""
    v = np.asarray(values, float)
    v = v[np.isfinite(v)]
    n = len(v)
    if n == 0:
        return (np.nan, np.nan, np.nan, 0)
    if n == 1:
        return (float(v[0]), np.nan, np.nan, 1)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_boot, n))
    means = v[idx].mean(axis=1)
    a = (1 - level) / 2
    return (float(v.mean()), float(np.quantile(means, a)), float(np.quantile(means, 1 - a)), n)
