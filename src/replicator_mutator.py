"""Large-population dynamics.

1. Replicator-mutator equations of Lee et al. (2019), Methods p.13281 ("Large-Population Limit"):
     dx_i/dt = x_i [ (Q(y) x)_i - x.Q(y)x ] - mu x_i + mu (1 - x_i)/3
     dy/dt   = y (1 - y) [P_H(x) - P_C(x)] - nu y + nu (1 - y)
   with Q(y) = y Q_H + (1 - y) Q_C (DECISIONS D-001) and y the honest fraction.

2. Fermi-imitation mean field: the exact large-population limit of our individual-based model
   (DECISIONS D-012). With F(d) = 1 / (1 + exp(-s d)), the imitation flux is
     x_i sum_j x_j [F(P_i - P_j) - F(P_j - P_i)] = x_i sum_j x_j tanh(s (P_i - P_j) / 2),
   and exploration contributes mu ((1 - x_i)/3 - x_i). An updating individual explores with
   probability mu, otherwise imitates, so imitation is weighted by (1 - mu).

Both systems optionally include an umpire rotation term rho (p_new - y) (see rotation.py).
The state vector is z = (x1, x2, x3, x4, y).
"""
from __future__ import annotations

import numpy as np
from numba import njit
from scipy.integrate import solve_ivp

from .params import Params
from .payoffs import Q_C, Q_H

# Rotation variant codes shared with rotation.py
ROT_NONE, ROT_V0, ROT_V1, ROT_V2 = 0, 1, 2, 3


@njit(cache=True)
def conformist(y, k):
    """g(y) = y^k / (y^k + (1 - y)^k) (CLAUDE.md Section 6, V2)."""
    if y <= 0.0:
        return 0.0
    if y >= 1.0:
        return 1.0
    a = y ** k
    return a / (a + (1.0 - y) ** k)


@njit(cache=True)
def p_new_value(variant, y, p0, kappa, kexp):
    """Honesty probability of a newcomer for undelayed variants (ASSUMPTION, CLAUDE.md Sec. 6)."""
    if variant == ROT_V0:
        return p0
    if variant == ROT_V1:
        return (1.0 - kappa) * p0 + kappa * y
    if variant == ROT_V2:
        return (1.0 - kappa) * p0 + kappa * conformist(y, kexp)
    return 0.0


@njit(cache=True)
def _payoffs(xh, y, QH, QC):
    fit = np.zeros(4)
    for i in range(4):
        acc = 0.0
        for k in range(4):
            acc += (y * QH[i, k] + (1.0 - y) * QC[i, k]) * xh[k]
        fit[i] = acc
    return fit


@njit(cache=True)
def _normalized(z):
    """Return (x / S, S) with S = sum(x).

    Payoffs are evaluated at x / S and the mutation term uses S, so that dS/dt = 0 exactly.
    On the simplex (S = 1) this is identical to the published equations. Without it, S = 1 is
    an unstable invariant set whenever the mean payoff is negative, and round-off grows.
    """
    S = z[0] + z[1] + z[2] + z[3]
    xh = np.empty(4)
    for i in range(4):
        xh[i] = z[i] / S
    return xh, S


@njit(cache=True)
def umpire_diff(z, f, B):
    """P_H - P_C as printed in Methods p.13281."""
    x1, x2, x3, x4 = z[0], z[1], z[2], z[3]
    return 2.0 * f * (x2 - x4) * (1.0 + x1 + x3) - 2.0 * B * (x3 + x4) * (1.0 - x2)


@njit(cache=True)
def rhs_rm(z, QH, QC, f, B, mu, nu, rho, variant, p0, kappa, kexp, ylag):
    """Replicator-mutator right-hand side (+ optional rotation term).

    ylag is used only by the delayed variant (handled in dde.py by passing variant = ROT_V1 with
    the delayed value substituted); for undelayed variants it is ignored.
    """
    out = np.zeros(5)
    y = z[4]
    xh, S = _normalized(z)
    fit = _payoffs(xh, y, QH, QC)
    fbar = 0.0
    for i in range(4):
        fbar += xh[i] * fit[i]
    for i in range(4):
        out[i] = z[i] * (fit[i] - fbar) - mu * z[i] + mu * (S - z[i]) / 3.0
    out[4] = y * (1.0 - y) * umpire_diff(xh, f, B) - nu * y + nu * (1.0 - y)
    if rho > 0.0:
        if variant == -1:  # delayed linear inheritance (V3): p_new uses y(t - T_lag)
            pn = (1.0 - kappa) * p0 + kappa * ylag
        else:
            pn = p_new_value(variant, y, p0, kappa, kexp)
        out[4] += rho * (pn - y)
    return out


@njit(cache=True)
def rhs_fermi(z, QH, QC, f, B, mu, nu, s, rho, variant, p0, kappa, kexp, ylag):
    """Exact mean field of the Fermi imitation-exploration IBM (DECISIONS D-012)."""
    out = np.zeros(5)
    y = z[4]
    xh, S = _normalized(z)
    fit = _payoffs(xh, y, QH, QC)
    for i in range(4):
        acc = 0.0
        for j in range(4):
            acc += xh[j] * np.tanh(0.5 * s * (fit[i] - fit[j]))
        out[i] = (1.0 - mu) * z[i] * acc + mu * ((S - z[i]) / 3.0 - z[i])
    x2, x4 = xh[1], xh[3]
    PH = 2.0 * f * (1.0 - x4) ** 2
    PC = 2.0 * f * (1.0 - x2) ** 2 + 2.0 * B * (xh[2] + xh[3]) * (1.0 - x2)
    out[4] = (1.0 - nu) * y * (1.0 - y) * np.tanh(0.5 * s * (PH - PC)) + nu * (1.0 - 2.0 * y)
    if rho > 0.0:
        if variant == -1:
            pn = (1.0 - kappa) * p0 + kappa * ylag
        else:
            pn = p_new_value(variant, y, p0, kappa, kexp)
        out[4] += rho * (pn - y)
    return out


class Model:
    """Bundles parameters for fast repeated evaluation of the right-hand side."""

    def __init__(self, p: Params, kind: str = "rm", s: float | None = None,
                 rho: float = 0.0, variant: int = ROT_NONE, p0: float = 1.0,
                 kappa: float = 0.0, kexp: float = 2.0):
        self.p = p
        self.kind = kind
        self.s = s
        self.QH = np.ascontiguousarray(Q_H(p))
        self.QC = np.ascontiguousarray(Q_C(p))
        self.rho = float(rho)
        self.variant = int(variant)
        self.p0 = float(p0)
        self.kappa = float(kappa)
        self.kexp = float(kexp)
        if kind == "fermi" and s is None:
            raise ValueError("Fermi mean field needs s")

    def f(self, t, z, ylag=0.0):
        p = self.p
        if self.kind == "rm":
            return rhs_rm(z, self.QH, self.QC, p.f, p.B, p.mu, p.nu, self.rho,
                          self.variant, self.p0, self.kappa, self.kexp, ylag)
        return rhs_fermi(z, self.QH, self.QC, p.f, p.B, p.mu, p.nu, self.s, self.rho,
                         self.variant, self.p0, self.kappa, self.kexp, ylag)


def integrate(model: Model, z0, t_end: float, t_eval=None, method: str = "LSODA",
              rtol: float = 1e-9, atol: float = 1e-12, max_step: float = np.inf,
              dense_output: bool = False):
    """Integrate an undelayed model with scipy's solve_ivp. Returns the OdeResult."""
    z0 = np.asarray(z0, dtype=float)
    sol = solve_ivp(lambda t, z: model.f(t, z), (0.0, t_end), z0, method=method,
                    t_eval=t_eval, rtol=rtol, atol=atol, max_step=max_step,
                    dense_output=dense_output)
    if not sol.success:
        raise RuntimeError(f"integration failed: {sol.message}")
    return sol


def state(x, y) -> np.ndarray:
    return np.concatenate([np.asarray(x, dtype=float), [float(y)]])
