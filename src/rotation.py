"""Umpire rotation (term limits) with inherited integrity: mean-field versions.

ASSUMPTION (author's extension, CLAUDE.md Section 6; not part of Lee et al. 2019):
- Continuous rotation: each umpire is replaced at rate rho; dy/dt gains rho (p_new - y).
- Pulse rotation: every T time units a fraction tau of umpires is replaced at once:
  y -> (1 - tau) y + tau p_new. Average rate rho = tau / T.
- Newcomer honesty p_new:
    V0 fresh cohort:          p0
    V1 linear inheritance:    (1 - kappa) p0 + kappa y
    V2 conformist inheritance:(1 - kappa) p0 + kappa g(y), g(y) = y^k / (y^k + (1 - y)^k), k = 2
    V3 delayed inheritance:   (1 - kappa) p0 + kappa y(t - T_lag), T_lag = one term
                              (1/rho for continuous rotation, T for pulses; DECISIONS D-010).
- For pulses with V3, y(t - T) is the honest fraction just before the previous pulse (the
  composition of the previous cohort at the end of its term; same convention as the IBM).

Analytical note (verified in tests/test_rho_eff_equivalence.py): for V1,
rho (p_new - y) = rho (1 - kappa)(p0 - y), so V1 equals V0 at rho_eff = rho (1 - kappa); the same
identity holds for the pulse map with tau_eff = tau (1 - kappa).
"""
from __future__ import annotations

import numpy as np
from scipy.integrate import solve_ivp

from .dde import integrate_dde
from .params import Params
from .replicator_mutator import ROT_NONE, ROT_V0, ROT_V1, ROT_V2, Model, conformist

VARIANT_CODES = {"none": ROT_NONE, "V0": ROT_V0, "V1": ROT_V1, "V2": ROT_V2, "V3": -1}


def make_model(p: Params, variant: str = "V0", rho: float = 0.0, kappa: float = 0.0,
               p0: float = 1.0, kexp: float = 2.0, kind: str = "rm", s=None) -> Model:
    return Model(p, kind=kind, s=s, rho=rho, variant=VARIANT_CODES[variant], p0=p0,
                 kappa=kappa, kexp=kexp)


def p_new(variant: str, y: float, p0: float, kappa: float, kexp: float = 2.0,
          ylag: float | None = None) -> float:
    if variant == "V0":
        return p0
    if variant == "V1":
        return (1 - kappa) * p0 + kappa * y
    if variant == "V2":
        return (1 - kappa) * p0 + kappa * conformist(y, kexp)
    if variant == "V3":
        return (1 - kappa) * p0 + kappa * (y if ylag is None else ylag)
    raise ValueError(variant)


def simulate_meanfield(p: Params, variant: str, rho: float, kappa: float = 0.0, p0: float = 1.0,
                       z0=None, t_burn: float = 10000.0, t_win: float = 10000.0,
                       dt: float = 0.5, T_lag: float | None = None, kexp: float = 2.0,
                       method: str = "LSODA", rtol: float = 1e-9, atol: float = 1e-11):
    """Integrate continuous-rotation mean field; return (t, Z) on the averaging window."""
    if z0 is None:
        z0 = np.array([0.1, 0.4, 0.4, 0.1, 1.0])
    m = make_model(p, variant, rho, kappa, p0, kexp)
    t_end = t_burn + t_win
    t_eval = np.arange(t_burn, t_end + 1e-9, dt)
    if variant == "V3" and rho > 0 and kappa > 0:
        tau = (1.0 / rho) if T_lag is None else T_lag
        if tau > 0:
            return integrate_dde(m, z0, tau, t_end, t_eval=t_eval, method=method, rtol=rtol,
                                 atol=atol)
        m = make_model(p, "V1", rho, kappa, p0, kexp)
    sol = solve_ivp(lambda t, z: m.f(t, z), (0.0, t_end), np.asarray(z0, float), method=method,
                    t_eval=t_eval, rtol=rtol, atol=atol)
    if not sol.success:
        raise RuntimeError(sol.message)
    return sol.t, sol.y.T


def simulate_pulse_meanfield(p: Params, variant: str, tau: float, T: float,
                             kappa: float = 0.0, p0: float = 1.0, z0=None,
                             t_burn: float = 10000.0, t_win: float = 10000.0, dt: float = 0.5,
                             kexp: float = 2.0, rtol: float = 1e-9, atol: float = 1e-11):
    """Impulsive mean field: base dynamics between pulses, jump y -> (1 - tau) y + tau p_new at
    t = T, 2T, ... Returns (t, Z) on the window (values just after any pulse at a sample time)."""
    if z0 is None:
        z0 = np.array([0.1, 0.4, 0.4, 0.1, 1.0])
    m = Model(p)  # no continuous rotation between pulses
    t_end = t_burn + t_win
    t_eval = np.arange(t_burn, t_end + 1e-9, dt)
    Z = np.empty((len(t_eval), 5))
    filled = np.zeros(len(t_eval), bool)
    z = np.asarray(z0, float).copy()
    y_prev_pre = z[4]  # V3: honest fraction just before the previous pulse (initially y0)
    t0 = 0.0
    while t0 < t_end - 1e-12:
        t1 = min(t0 + T, t_end)
        sol = solve_ivp(lambda t, zz: m.f(t, zz), (t0, t1), z, method="LSODA", rtol=rtol,
                        atol=atol, dense_output=True)
        mask = (t_eval >= t0 - 1e-12) & (t_eval < t1 - 1e-12) & ~filled
        if mask.any():
            Z[mask] = sol.sol(t_eval[mask]).T
            filled |= mask
        z = sol.y[:, -1].copy()
        if t1 < t_end - 1e-12 or abs(t1 - (t0 + T)) < 1e-12:
            y_pre = z[4]
            pn = p_new(variant, y_pre, p0, kappa, kexp, ylag=y_prev_pre)
            z[4] = (1 - tau) * y_pre + tau * pn
            y_prev_pre = y_pre
        t0 = t1
    last = ~filled
    if last.any():
        Z[last] = z
    return t_eval, Z
