"""Delay differential equations by the method of steps (V3 delayed inheritance).

V3 (SPEC.md Section 11, ASSUMPTION): dy/dt = [base] + rho ((1 - kappa) p0 + kappa y(t - T_lag) - y).
Only y is delayed. History: constant initial state for t <= 0.

Method of steps: integrate on [k tau, (k+1) tau] with solve_ivp (dense output); the delayed value
y(t - tau) is read from the dense output of the previous interval, which is smooth there. Restarting
at multiples of tau handles the derivative jumps that propagate from t = 0.
"""
from __future__ import annotations

import numpy as np
from scipy.integrate import solve_ivp

from .replicator_mutator import Model


def integrate_dde(model: Model, z0, tau: float, t_end: float, t_eval=None,
                  method: str = "LSODA", rtol: float = 1e-9, atol: float = 1e-11,
                  history=None):
    """Integrate model with delayed y. model must have variant = -1 (V3) or any variant whose
    rhs accepts ylag. Returns (t, Z) at t_eval (default: every 0.5 time units)."""
    z0 = np.asarray(z0, float)
    if t_eval is None:
        t_eval = np.arange(0.0, t_end + 1e-12, 0.5)
    t_eval = np.asarray(t_eval, float)
    if history is None:
        y_hist = float(z0[4])
        history = lambda t: y_hist
    prev = None
    Z = np.empty((len(t_eval), 5))
    filled = np.zeros(len(t_eval), bool)
    t0 = 0.0
    z = z0.copy()
    while t0 < t_end - 1e-12:
        t1 = min(t0 + tau, t_end)
        if prev is None:
            ylag_fn = lambda t: history(t - tau)
        else:
            sol_prev = prev
            ylag_fn = lambda t, s=sol_prev: s(t - tau)[4]
        sol = solve_ivp(lambda t, zz: model.f(t, zz, ylag_fn(t)), (t0, t1), z, method=method,
                        rtol=rtol, atol=atol, dense_output=True)
        if not sol.success:
            raise RuntimeError(sol.message)
        mask = (t_eval >= t0 - 1e-12) & (t_eval <= t1 + 1e-12) & ~filled
        if mask.any():
            Z[mask] = sol.sol(t_eval[mask]).T
            filled |= mask
        prev = sol.sol
        z = sol.y[:, -1]
        t0 = t1
    return t_eval, Z
