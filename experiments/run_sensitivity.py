"""E7: robustness and sensitivity (R3, R4, R5).

Usage: python experiments/run_sensitivity.py [quick|full] [section ...]
Sections: oat pulse altA p0 finite explo numerics se (default: all).
Writes results/<profile>/sens_*.json.
"""
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from src import analysis as an
from src.ibm import run_ibm
from src.metrics import bootstrap_ci
from src.params import check_inequalities
from src.rotation import make_model
from src.runners import ibm_replicate, mf_point, parallel, params_from
from src.utils import load_config, save_result

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_extension import (FIG3_START, ibm_condition, mf_kw, mf_params,  # noqa: E402
                           run_conditions, summarize_reps)

RHO_PROBE = 0.05   # a rotation rate above rho_c at base parameters (rho_c = 0.0133)


def _critical(p, p0=1.0):
    """Folds (rho) of the V0 equilibrium curve and the small-mu approximation."""
    def mk(r):
        return make_model(p, "V0", r, p0=p0)
    try:
        u0 = an.find_equilibria(mk(0.0))[0]
        br = an.continue_equilibria(mk, u0, 0.0, 0.0, 1.0, ds=1e-3)
        folds = sorted(f[0] for f in (an.refine_fold(mk, br["u"][i], br["lam"][i])
                                      for i in br["fold_idx"]) if f)
        hopfs = sorted(h[0] for h in (an.refine_hopf(mk, br["u"][i], br["lam"][i])
                                      for i in br["hopf_idx"]) if h)
        stable0 = bool(br["stable"][0])
    except Exception as e:
        folds, hopfs, stable0 = [], [], None
    try:
        approx = an.rho_c_approx(p, p0)[0]
    except Exception:
        approx = None
    return {"folds": folds, "hopfs": hopfs, "stable_at_0": stable0, "approx": approx}


def _oat_point(cfg, name, value, p):
    kw = mf_kw(cfg)
    a = mf_point(p, "V0", 0.0, **kw)
    b = mf_point(p, "V0", RHO_PROBE, **kw)
    crit = _critical(p)
    return {"param": name, "value": value, "admissible": check_inequalities(p),
            "ybar_rho0": a["ybar"], "Cbar_rho0": a["Cbar"], "attractor_rho0": a["attractor"],
            "ybar_probe": b["ybar"], "Cbar_probe": b["Cbar"], "attractor_probe": b["attractor"],
            "gain": b["ybar"] - a["ybar"], **{f"crit_{k}": v for k, v in crit.items()}}


def oat(cfg):
    base = mf_params(cfg)
    tasks = [(_oat_point, dict(cfg=cfg, name="base", value=None, p=base))]
    for name in ("b", "c", "f", "B", "h", "A", "mu", "nu"):
        for fac in (0.8, 1.2):
            v = getattr(base, name) * fac
            tasks.append((_oat_point, dict(cfg=cfg, name=name, value=fac,
                                           p=base.with_(**{name: v}))))
    res = parallel(tasks, cfg["n_jobs"])
    # s: only matters in the IBM. Large setting (s = 0.3) +-20%; small setting (s = 1e10).
    out = {"meanfield": res, "rho_probe": RHO_PROBE}
    conds = []
    L = cfg["ibm_large"]
    for fac in (0.8, 1.0, 1.2):
        for r in (0.0, 0.1):
            S = dict(L, s=L["s"] * fac)
            run = cfg["ibm_large_run"]
            tasks = [(ibm_replicate, dict(p=params_from(cfg), setting=S, run=run,
                                          seed=cfg["seed"] + 61 + 7919 * k, rho=r))
                     for k in range(cfg["reps"])]
            conds.append(({"s_factor": fac, "rho": r}, tasks))
    out["ibm_large_s"] = run_conditions(cfg, conds)
    S = cfg["ibm_small"]
    p = params_from(cfg, mu=S["mu"], nu=S["nu"])
    ys = {}
    for fac in (0.8, 1.0, 1.2):
        r = run_ibm(p, S["M"], S["N"], S["s"] * fac, 2000.0, 0.5, cfg["seed"] + 5,
                    ibm_variant=S["ibm_variant"])
        ys[fac] = r["n_honest"]
    out["ibm_small_s_identical"] = bool(np.array_equal(ys[0.8], ys[1.0])
                                        and np.array_equal(ys[1.2], ys[1.0]))
    return out


def pulse(cfg):
    p = mf_params(cfg)
    kw = mf_kw(cfg)
    out = {"meanfield": []}
    tasks, keys = [], []
    for r in (0.02, 0.05, 0.1):
        tasks.append((mf_point, dict(p=p, variant="V0", rho=r, **kw)))
        keys.append((r, None))
        for tau in (0.1, 0.25, 0.5, 1.0):
            tasks.append((mf_point, dict(p=p, variant="V0", rho=r, pulse_T=tau / r, **kw)))
            keys.append((r, tau))
    res = parallel(tasks, cfg["n_jobs"])
    for (r, tau), q in zip(keys, res):
        out["meanfield"].append({"rho": r, "tau": tau, "T": None if tau is None else tau / r,
                                 **{k: q[k] for k in ("ybar", "Cbar", "A_y", "x2bar",
                                                      "attractor", "C_min")}})
    conds = []
    for r in (0.03, 0.1):
        conds.append(({"rho": r, "tau": None}, ibm_condition(cfg, "ibm_small", rho=r,
                                                             seed_offset=71)))
        for tau in (0.1, 0.2, 0.5, 1.0):
            conds.append(({"rho": r, "tau": tau}, ibm_condition(
                cfg, "ibm_small", rho=r, pulse_T=tau / r, pulse_tau=tau, seed_offset=71)))
    # V1 pulse equivalence in the IBM: (tau, kappa) vs V0 at tau (1 - kappa)
    for tau, k in ((0.5, 0.6), (1.0, 0.5), (1.0, 0.8)):
        r = 0.1
        conds.append(({"rho": r, "tau": tau, "kappa": k, "variant": "V1"}, ibm_condition(
            cfg, "ibm_small", rho=r, pulse_T=tau / r, pulse_tau=tau, variant="V1", kappa=k,
            seed_offset=73)))
        conds.append(({"rho": r, "tau": tau * (1 - k), "kappa": 0.0, "variant": "V0eff",
                       "pulse_T": tau / r}, ibm_condition(
            cfg, "ibm_small", rho=r, pulse_T=tau / r, pulse_tau=tau * (1 - k), variant="V0",
            seed_offset=79)))
    out["ibm_small"] = run_conditions(cfg, conds)
    return out


def _ybar_curve(cfg, p, rhos, p0=1.0, t_burn=None, t_win=None):
    kw = mf_kw(cfg)
    if t_burn:
        kw.update(t_burn=t_burn, t_win=t_win)
    tasks = [(mf_point, dict(p=p, variant="V0", rho=float(r), p0=p0, **kw)) for r in rhos]
    res = parallel(tasks, cfg["n_jobs"])
    return [{"rho": float(r), **{k: q[k] for k in ("ybar", "Cbar", "A_y", "x2bar", "attractor")}}
            for r, q in zip(rhos, res)]


def altA(cfg):
    p = mf_params(cfg, A=0.7)
    rhos = np.linspace(0, 0.15, 31 if cfg["profile"] == "full" else 7)
    out = {"meanfield": _ybar_curve(cfg, p, rhos), "critical": _critical(p)}
    conds = [({"rho": r}, ibm_condition(cfg, "ibm_small", A=0.7, rho=r, seed_offset=83))
             for r in cfg["grids"]["ibm_rho"]]
    out["ibm_small"] = run_conditions(cfg, conds)
    return out


def p0(cfg):
    p = mf_params(cfg)
    rhos = np.linspace(0, 0.15, 31 if cfg["profile"] == "full" else 7)
    out = {"meanfield": {}, "critical": {}, "ibm_small": []}
    for q0 in (1.0, 0.9, 0.75, 0.6):
        out["meanfield"][str(q0)] = _ybar_curve(cfg, p, rhos, p0=q0)
        out["critical"][str(q0)] = _critical(p, p0=q0)
    conds = [({"p0": q0, "rho": r}, ibm_condition(cfg, "ibm_small", rho=r, p0=q0,
                                                  seed_offset=89))
             for q0 in (0.9, 0.75, 0.6) for r in (0.03, 0.1, 0.3)]
    out["ibm_small"] = run_conditions(cfg, conds)
    return out


def finite(cfg):
    conds = []
    S = cfg["ibm_small"]
    for M in cfg["grids"]["finite_M"]:
        setting = dict(S, M=M, N=M // 5)
        for r in (0.0, 0.03, 0.1, 0.3):
            run = cfg["ibm_small_run"]
            tasks = [(ibm_replicate, dict(p=params_from(cfg), setting=setting, run=run,
                                          seed=cfg["seed"] + 97 + M + 7919 * k, rho=r))
                     for k in range(cfg["reps"])]
            conds.append(({"M": M, "N": M // 5, "rho": r}, tasks))
    return {"ibm": run_conditions(cfg, conds)}


def explo(cfg):
    out = {}
    for mu in (0.001, 0.02):
        p = mf_params(cfg, mu=mu, nu=mu)
        tb = 40000 if mu < 0.005 else None
        if cfg["profile"] != "full" and tb:
            tb = 10000
        rhos = np.linspace(0, 0.08, 33 if cfg["profile"] == "full" else 9)
        out[str(mu)] = {"meanfield": _ybar_curve(cfg, p, rhos, t_burn=tb, t_win=tb),
                        "critical": _critical(p)}
    return out


def numerics(cfg):
    """R4: tolerance tightening (10x) and solver change on a subset of E1; finer grid."""
    kw = mf_kw(cfg)
    pts = [(h, r) for h in (0.05, 0.1, 0.2, 0.27) for r in (0.0, 0.01, 0.02, 0.05)]
    tasks = []
    for h, r in pts:
        p = mf_params(cfg, h=h)
        tasks.append((mf_point, dict(p=p, variant="V0", rho=r, **kw)))
        kw2 = dict(kw, rtol=kw["rtol"] / 10, atol=kw["atol"] / 10)
        tasks.append((mf_point, dict(p=p, variant="V0", rho=r, **kw2)))
        tasks.append((mf_point, dict(p=p, variant="V0", rho=r, method="DOP853", **kw2)))
    res = parallel(tasks, cfg["n_jobs"])
    rows = []
    for i, (h, r) in enumerate(pts):
        a, b, c = res[3 * i:3 * i + 3]
        rows.append({"h": h, "rho": r, "ybar": [a["ybar"], b["ybar"], c["ybar"]],
                     "A_y": [a["A_y"], b["A_y"], c["A_y"]],
                     "C_min": [a["C_min"], b["C_min"], c["C_min"]],
                     "max_abs_diff": float(max(abs(a[k] - x[k]) for x in (b, c)
                                               for k in ("ybar", "A_y", "C_min")))})
    # finer grid in a sub-region: boundary of the cycle region vs continuation
    hs = np.linspace(0.05, 0.15, 11 if cfg["profile"] == "full" else 3)
    rhos = np.linspace(0.0, 0.03, 25 if cfg["profile"] == "full" else 7)
    tasks = [(mf_point, dict(p=mf_params(cfg, h=float(h)), variant="V0", rho=float(r), **kw))
             for h in hs for r in rhos]
    res = parallel(tasks, cfg["n_jobs"])
    fine = []
    for i, h in enumerate(hs):
        sub = res[i * len(rhos):(i + 1) * len(rhos)]
        eq = [float(r) for r, q in zip(rhos, sub) if q["attractor"] == "equilibrium"]
        crit = _critical(mf_params(cfg, h=float(h)))
        fine.append({"h": float(h), "first_equilibrium_rho": min(eq) if eq else None,
                     "rho_c": crit["folds"][0] if crit["folds"] else None,
                     "grid_step": float(rhos[1] - rhos[0])})
    return {"tolerance": rows, "fine_grid": fine}


def se(cfg):
    """R3: standard error of ybar vs number of replicates at rho = 0.03 (small IBM)."""
    S = cfg["ibm_small"]
    n = 50 if cfg["profile"] == "full" else 10
    tasks = [(ibm_replicate, dict(p=params_from(cfg), setting=S, run=cfg["ibm_small_run"],
                                  seed=cfg["seed"] + 101 + 7919 * k, rho=0.03))
             for k in range(n)]
    res = parallel(tasks, cfg["n_jobs"])
    out = {}
    for key in ("ybar", "x2bar", "episode_freq_per_1000", "depth_C"):
        v = np.array([r[key] for r in res])
        v = v[np.isfinite(v)]
        out[key] = {int(k): float(np.std(v[:k], ddof=1) / np.sqrt(k))
                    for k in (5, 10, 20, 30, 50) if k <= len(v)}
    return out


SECTIONS = {"oat": oat, "pulse": pulse, "altA": altA, "p0": p0, "finite": finite,
            "explo": explo, "numerics": numerics, "se": se}


def main(profile, sections):
    cfg = load_config(profile)
    t0 = time.time()
    for s in sections:
        t1 = time.time()
        data = SECTIONS[s](cfg)
        data["runtime_s"] = time.time() - t1
        path = save_result(f"sens_{s}", data, cfg)
        print(f"sens_{s}: {time.time() - t1:.1f} s -> {path}", flush=True)
    print(f"total {time.time() - t0:.1f} s")


if __name__ == "__main__":
    prof = sys.argv[1] if len(sys.argv) > 1 else "quick"
    secs = sys.argv[2:] or list(SECTIONS)
    main(prof, secs)
