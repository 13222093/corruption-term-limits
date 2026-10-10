"""Helpers that run one IBM replicate or one mean-field point and return METRICS.md metrics."""
from __future__ import annotations

import numpy as np
from joblib import Parallel, delayed

from .ibm import ROT_CONT, ROT_OFF, ROT_PULSE, V0, V1, V2, V3, run_ibm
from .metrics import classify_attractor, summarize
from .params import Params
from .rotation import simulate_meanfield, simulate_pulse_meanfield

VAR_IBM = {"V0": V0, "V1": V1, "V2": V2, "V3": V3}


def params_from(cfg: dict, **over) -> Params:
    d = dict(cfg["params"])
    d.update(over)
    return Params(**d)


def ibm_replicate(p: Params, setting: dict, run: dict, seed: int, rho: float = 0.0,
                  variant: str = "V0", kappa: float = 0.0, p0: float = 1.0,
                  pulse_T: float | None = None, pulse_tau: float = 0.0,
                  T_lag: float | None = None, x0=None, y0: float = 1.0,
                  keep_series: int = 0) -> dict:
    """Run one IBM replicate and summarize the window after burn-in.

    setting: dict with M, N, mu, nu, s. run: dict with burn, win, rec_dt (generations).
    Continuous rotation if pulse_T is None, otherwise pulses of fraction pulse_tau every pulse_T.
    keep_series: if > 0, also return the series downsampled to at most that many points.
    """
    pp = p.with_(mu=setting["mu"], nu=setting["nu"])
    if pulse_T is not None:
        mode = ROT_PULSE
    else:
        mode = ROT_CONT if rho > 0 else ROT_OFF
    if T_lag is None:
        T_lag = (pulse_T if pulse_T is not None else (1.0 / rho if rho > 0 else 0.0))
    t_end = run["burn"] + run["win"]
    r = run_ibm(pp, setting["M"], setting["N"], setting["s"], t_end, run["rec_dt"], seed,
                x0=x0, y0=y0, rot_mode=mode, rho=rho, variant=VAR_IBM[variant], p0=p0,
                kappa=kappa, T_lag=T_lag, pulse_T=pulse_T or 1.0, pulse_tau=pulse_tau)
    w = r["t"] >= run["burn"]
    out = summarize(r["t"][w], r["x"][w], r["y"][w], pp, kind="ibm")
    out["seed"] = int(seed)
    out["n_events"] = r["n_events"]
    if keep_series:
        step = max(1, int(np.ceil(len(r["t"]) / keep_series)))
        out["series"] = {"t": r["t"][::step].tolist(), "x": r["x"][::step].tolist(),
                         "y": r["y"][::step].tolist()}
    return out


def mf_point(p: Params, variant: str, rho: float, kappa: float = 0.0, p0: float = 1.0,
             z0=None, t_burn: float = 10000, t_win: float = 10000, dt: float = 0.5,
             T_lag: float | None = None, rtol: float = 1e-9, atol: float = 1e-11,
             method: str = "LSODA", pulse_T: float | None = None, keep_series: int = 0,
             kexp: float = 2.0) -> dict:
    """Mean-field run: metrics on the window plus attractor classification."""
    if pulse_T is None:
        t, Z = simulate_meanfield(p, variant, rho, kappa, p0, z0=z0, t_burn=t_burn,
                                  t_win=t_win, dt=dt, T_lag=T_lag, kexp=kexp, rtol=rtol,
                                  atol=atol, method=method)
    else:
        t, Z = simulate_pulse_meanfield(p, variant, rho * pulse_T, pulse_T, kappa, p0, z0=z0,
                                        t_burn=t_burn, t_win=t_win, dt=dt, kexp=kexp,
                                        rtol=rtol, atol=atol)
    out = summarize(t, Z[:, :4], Z[:, 4], p, kind="ode")
    c = classify_attractor(t, Z[:, 4])
    out["attractor"] = c["type"]
    out["period"] = c["period"]
    out["z_end"] = Z[-1].tolist()
    if keep_series:
        step = max(1, int(np.ceil(len(t) / keep_series)))
        out["series"] = {"t": t[::step].tolist(), "z": Z[::step].tolist()}
    return out


def parallel(tasks, n_jobs: int = 14, verbose: int = 0):
    """Run a list of (callable, kwargs) in parallel processes; returns results in order."""
    return Parallel(n_jobs=n_jobs, verbose=verbose)(delayed(f)(**kw) for f, kw in tasks)
