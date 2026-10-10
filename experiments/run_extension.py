"""Extension experiments E1-E6 and the mean-field bifurcation analysis (R2).

Usage: python experiments/run_extension.py [quick|full] [section ...]
Sections: bif e1 e2 e3 e4 e5 e6 (default: all). Writes results/<profile>/ext_*.json.
All metrics follow METRICS.md. Mean-field and IBM results are stored separately.
"""
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from src import analysis as an
from src.metrics import bootstrap_ci
from src.rotation import make_model
from src.runners import ibm_replicate, mf_point, parallel, params_from
from src.utils import load_config, save_result

HONEST_START = np.array([0.97, 0.01, 0.01, 0.01, 0.99])   # METRICS.md Section 2
CORRUPT_START = np.array([0.01, 0.73, 0.25, 0.01, 0.01])
FIG3_START = np.array([0.1, 0.4, 0.4, 0.1, 1.0])

IBM_KEYS = ["ybar", "Cbar", "Rbar", "Wbar", "x2bar", "A_y", "A_C", "C_min", "y_sd",
            "episode_freq_per_1000", "depth_y", "depth_C", "recovery_time",
            "corrupt_majority_time", "n_episodes"]


def mf_params(cfg, **over):
    o = dict(mu=cfg["ode"]["mu"], nu=cfg["ode"]["nu"])
    o.update(over)
    return params_from(cfg, **o)


def mf_kw(cfg):
    o = cfg["ode"]
    return dict(t_burn=o["t_burn"], t_win=o["t_win"], dt=o["dt"], rtol=o["rtol"], atol=o["atol"])


def summarize_reps(res, keys=IBM_KEYS):
    out = {}
    for k in keys:
        vals = [r[k] for r in res]
        m, lo, hi, n = bootstrap_ci(vals)
        out[k] = {"mean": m, "lo": lo, "hi": hi, "n": n}
    return out


def ibm_condition(cfg, setting_name, reps=None, seed_offset=0, **kw):
    """Run replicates of one IBM condition in parallel; returns per-replicate metrics."""
    S = cfg[setting_name]
    run = cfg["ibm_small_run"] if setting_name == "ibm_small" else cfg["ibm_large_run"]
    p = params_from(cfg, **{k: kw.pop(k) for k in list(kw) if k in ("h", "A", "b", "c", "f", "B")})
    reps = reps or cfg["reps"]
    tasks = [(ibm_replicate, dict(p=p, setting=S, run=run, seed=cfg["seed"] + seed_offset + 7919 * k,
                                  **kw)) for k in range(reps)]
    return tasks


def run_conditions(cfg, conds):
    """conds: list of (label dict, tasks). Runs all tasks in one parallel pool."""
    flat = [t for _, tasks in conds for t in tasks]
    res = parallel(flat, cfg["n_jobs"])
    out, i = [], 0
    for label, tasks in conds:
        rr = res[i:i + len(tasks)]
        i += len(tasks)
        out.append({**label, "summary": summarize_reps(rr),
                    "per_rep": [{k: r[k] for k in IBM_KEYS} for r in rr]})
    return out


# ---------------------------------------------------------------------------
# Bifurcation analysis (Fig. 4)
# ---------------------------------------------------------------------------

def _branch(p, variant="V0", lam_max=0.6):
    def mk(r):
        return make_model(p, variant, r)
    u0 = an.find_equilibria(mk(0.0))[0]
    br = an.continue_equilibria(mk, u0, 0.0, 0.0, lam_max, ds=1e-3)
    folds = [an.refine_fold(mk, br["u"][i], br["lam"][i]) for i in br["fold_idx"]]
    hopfs = [an.refine_hopf(mk, br["u"][i], br["lam"][i]) for i in br["hopf_idx"]]
    return br, [f for f in folds if f], [h for h in hopfs if h]


def _twopar_point(p):
    br, folds, hopfs = _branch(p)
    approx = an.rho_c_approx(p)
    return {"mu": p.mu, "A": p.A, "folds": sorted(f[0] for f in folds),
            "hopfs": sorted(h[0] for h in hopfs), "rho_c_approx": approx[0],
            "rho0_stable": bool(br["stable"][0])}


def bif(cfg):
    p = mf_params(cfg)
    br, folds, hopfs = _branch(p)
    out = {"branch": {"rho": br["lam"].tolist(), "y": br["u"][:, 3].tolist(),
                      "x": [an.full_state(u)[:4].tolist() for u in br["u"]],
                      "stable": br["stable"].tolist()},
           "folds": [{"rho": f[0], "u": an.full_state(f[1]).tolist()} for f in folds],
           "hopfs": [{"rho": h[0], "omega": h[2]} for h in hopfs]}
    rc_approx, y_at = an.rho_c_approx(p)
    rho_c = min(f[0] for f in folds)
    out["rho_c"] = rho_c
    out["rho_c_approx"] = rc_approx
    out["rho_c_approx_y"] = y_at
    out["rho_c_approx_rel_err"] = (rc_approx - rho_c) / rho_c
    out["thresholds"] = dict(zip(("y_OD", "y_PD"), an.invasion_thresholds(p)))
    # attractor diagram from two starts
    n = cfg["grids"]["e4_rho_mf_n"]
    rhos = np.unique(np.r_[np.linspace(0, 0.2, n), np.linspace(0.8 * rho_c, 1.2 * rho_c, n // 3)])
    kw = mf_kw(cfg)
    tasks = []
    for r in rhos:
        for z0 in (FIG3_START, HONEST_START, CORRUPT_START):
            tasks.append((mf_point, dict(p=p, variant="V0", rho=float(r), z0=z0, **kw)))
    res = parallel(tasks, cfg["n_jobs"])
    att = []
    for i, r in enumerate(rhos):
        trip = res[3 * i:3 * i + 3]
        att.append({"rho": float(r), "starts": [
            {k: q[k] for k in ("ybar", "y_absmin", "y_absmax", "Cbar", "C_min", "A_y", "x2bar",
                               "period", "attractor", "depth_y", "depth_C", "recovery_time",
                               "episode_freq_per_1000", "Rbar", "Wbar", "z_end")}
            for q in trip]})
    out["attractors"] = att
    # SNIC scaling of the period below rho_c
    d = np.geomspace(1e-5, 3e-3, 10 if cfg["profile"] == "full" else 5)
    tasks = [(mf_point, dict(p=p, variant="V0", rho=float(rho_c - di), t_burn=20000,
                             t_win=60000, dt=0.5)) for di in d]
    res = parallel(tasks, cfg["n_jobs"])
    per = np.array([q["period"] for q in res])
    ok = np.isfinite(per)
    slope = np.polyfit(np.log(d[ok]), np.log(per[ok]), 1)[0] if ok.sum() >= 3 else np.nan
    out["snic"] = {"delta": d.tolist(), "period": per.tolist(), "loglog_slope": float(slope)}
    # two-parameter diagram (mu = nu, rho), A = 2 and A = 0.7
    mus = np.geomspace(1e-3, 0.065, cfg["grids"]["twopar_mu_n"])
    tasks = [(_twopar_point, dict(p=params_from(cfg, A=A, mu=float(m), nu=float(m))))
             for A in (2.0, 0.7) for m in mus]
    out["twopar"] = parallel(tasks, cfg["n_jobs"])
    return out


# ---------------------------------------------------------------------------
# E1: rho x h (V0), mean field and IBM
# ---------------------------------------------------------------------------

def _rho_c_of(p):
    try:
        br, folds, hopfs = _branch(p, lam_max=1.0)
        f = sorted(x[0] for x in folds)
        h = sorted(x[0] for x in hopfs)
        return {"folds": f, "hopfs": h, "stable_at_0": bool(br["stable"][0])}
    except Exception as e:  # no interior equilibrium etc.
        return {"folds": [], "hopfs": [], "error": str(e)}


def e1(cfg):
    G = cfg["grids"]
    kw = mf_kw(cfg)
    tasks, keys = [], []
    for h in G["e1_h"]:
        for r in G["e1_rho"]:
            tasks.append((mf_point, dict(p=mf_params(cfg, h=h), variant="V0", rho=r, **kw)))
            keys.append((h, r))
    res = parallel(tasks, cfg["n_jobs"])
    grid = [{"h": h, "rho": r, **{k: q[k] for k in ("ybar", "Cbar", "Rbar", "Wbar", "A_y",
                                                     "x2bar", "C_min", "attractor", "period")}}
            for (h, r), q in zip(keys, res)]
    crit = parallel([(_rho_c_of, dict(p=mf_params(cfg, h=h))) for h in G["e1_h"]],
                    cfg["n_jobs"])
    approx = []
    for h in G["e1_h"]:
        p = mf_params(cfg, h=h)
        try:
            approx.append(an.rho_c_approx(p)[0])
        except Exception:
            approx.append(None)
    out = {"meanfield": grid, "critical": [{"h": h, **c, "approx": a}
                                           for h, c, a in zip(G["e1_h"], crit, approx)]}
    conds = []
    for h in G["ibm_h"]:
        for r in G["ibm_rho"]:
            conds.append(({"h": h, "rho": r},
                          ibm_condition(cfg, "ibm_small", h=h, rho=r, seed_offset=11)))
    out["ibm_small"] = run_conditions(cfg, conds)
    return out


# ---------------------------------------------------------------------------
# E2: rho x kappa for V1, V2, V3; E5 hysteresis; IBM equivalence (H3)
# ---------------------------------------------------------------------------

def e2(cfg):
    G = cfg["grids"]
    p = mf_params(cfg)
    kw = mf_kw(cfg)
    out = {}
    for var in ("V1", "V2", "V3"):
        tasks, keys = [], []
        starts = (FIG3_START, HONEST_START, CORRUPT_START) if var == "V2" else (FIG3_START,)
        for k in G["e2_kappa"]:
            for r in G["e2_rho"]:
                for si, z0 in enumerate(starts):
                    tasks.append((mf_point, dict(p=p, variant=var, rho=r, kappa=k, z0=z0, **kw)))
                    keys.append((k, r, si))
        res = parallel(tasks, cfg["n_jobs"])
        grid = [{"kappa": k, "rho": r, "start": si,
                 **{q: v[q] for q in ("ybar", "Cbar", "A_y", "x2bar", "C_min", "attractor",
                                      "Rbar")}} for (k, r, si), v in zip(keys, res)]
        out[f"meanfield_{var}"] = grid
    # IBM: V1, V2, V3 and the V0 equivalent of V1 (rho_eff = rho (1 - kappa))
    conds = []
    rhos = [r for r in G["ibm_rho"] if r in (0.03, 0.1, 0.3)] or [0.03, 0.1, 0.3]
    for var in ("V1", "V2", "V3"):
        for r in rhos:
            for k in G["ibm_kappa"]:
                conds.append(({"variant": var, "rho": r, "kappa": k},
                              ibm_condition(cfg, "ibm_small", rho=r, variant=var, kappa=k,
                                            seed_offset=23)))
    for r in rhos:
        for k in G["ibm_kappa"]:
            conds.append(({"variant": "V0eff", "rho": r, "kappa": k, "rho_eff": r * (1 - k)},
                          ibm_condition(cfg, "ibm_small", rho=r * (1 - k), variant="V0",
                                        seed_offset=29)))
    out["ibm_small"] = run_conditions(cfg, conds)
    return out


def _v2_hysteresis(p, rho, kappas, t_burn, t_win):
    """Sweep kappa up then down, continuing from the previous end state (METRICS.md)."""
    up, down = [], []
    z = HONEST_START.copy()
    z = np.array(mf_point(p, "V0", 0.0, z0=FIG3_START, t_burn=2000, t_win=10)["z_end"])
    for k in kappas:
        q = mf_point(p, "V2", rho, k, z0=z, t_burn=t_burn, t_win=t_win)
        up.append({"kappa": k, "ybar": q["ybar"], "A_y": q["A_y"], "Cbar": q["Cbar"],
                   "attractor": q["attractor"]})
        z = np.array(q["z_end"])
    for k in kappas[::-1]:
        q = mf_point(p, "V2", rho, k, z0=z, t_burn=t_burn, t_win=t_win)
        down.append({"kappa": k, "ybar": q["ybar"], "A_y": q["A_y"], "Cbar": q["Cbar"],
                     "attractor": q["attractor"]})
        z = np.array(q["z_end"])
    return {"rho": rho, "up": up, "down": down[::-1]}


def _v2_folds_in_kappa(p, rho):
    """Continue the V2 honest equilibrium in kappa from kappa = 0 (needs rho > rho_c)."""
    def mk(k):
        return make_model(p, "V2", rho, k)
    eq = an.find_equilibria(mk(0.0), n_starts=80, extra_starts=[HONEST_START[[0, 1, 2, 4]]])
    eq = [u for u in eq if an.eigenvalues(mk(0.0), u)[0].real < 0 and u[3] > 0.5]
    if not eq:
        return {"rho": rho, "folds": [], "note": "no stable honest equilibrium at kappa = 0"}
    br = an.continue_equilibria(mk, eq[0], 0.0, 0.0, 1.0, ds=1e-3)
    folds = [an.refine_fold(mk, br["u"][i], br["lam"][i]) for i in br["fold_idx"]]
    return {"rho": rho, "folds": sorted(f[0] for f in folds if f),
            "branch_kappa": br["lam"].tolist(), "branch_y": br["u"][:, 3].tolist(),
            "branch_stable": br["stable"].tolist()}


def e5(cfg):
    p = mf_params(cfg)
    n = 41 if cfg["profile"] == "full" else 11
    kappas = list(np.linspace(0, 0.98, n))
    tb = 5000 if cfg["profile"] == "full" else 2000
    tasks = [(_v2_hysteresis, dict(p=p, rho=r, kappas=kappas, t_burn=tb, t_win=tb))
             for r in (0.02, 0.05, 0.1)]
    hyst = parallel(tasks, cfg["n_jobs"])
    rhos = np.linspace(0.015, 0.2, 24 if cfg["profile"] == "full" else 6)
    folds = parallel([(_v2_folds_in_kappa, dict(p=p, rho=float(r))) for r in rhos],
                     cfg["n_jobs"])
    out = {"hysteresis": hyst, "fold_curve": folds}
    # robustness scan for bistability (two starts) beyond the default parameters
    full = cfg["profile"] == "full"
    hs = (0.1, 0.2, 0.27, 0.29) if full else (0.1, 0.29)
    mus = (0.001, 0.01)
    kexps = (2.0, 4.0) if full else (2.0,)
    kaps = (0.5, 0.8, 0.95)
    rhos_s = (0.01, 0.02, 0.05, 0.1, 0.2) if full else (0.02, 0.1)
    tasks, keys = [], []
    for h in hs:
        for mu in mus:
            tb = 20000 if mu < 0.005 else 8000
            if not full:
                tb = tb // 4
            for ke in kexps:
                for k in kaps:
                    for r in rhos_s:
                        for name, z0 in (("honest", HONEST_START), ("corrupt", CORRUPT_START)):
                            tasks.append((mf_point, dict(p=mf_params(cfg, h=h, mu=mu, nu=mu),
                                                         variant="V2", rho=r, kappa=k, kexp=ke,
                                                         z0=z0, t_burn=tb, t_win=tb)))
                            keys.append((h, mu, ke, k, r, name))
    res = parallel(tasks, cfg["n_jobs"])
    scan = {}
    for (h, mu, ke, k, r, name), q in zip(keys, res):
        scan.setdefault((h, mu, ke, k, r), {})[name] = {"ybar": q["ybar"], "A_y": q["A_y"],
                                                         "attractor": q["attractor"]}
    out["bistability_scan"] = [{"h": h, "mu": mu, "kexp": ke, "kappa": k, "rho": r, **v,
                                "bistable": abs(v["honest"]["ybar"] - v["corrupt"]["ybar"]) > 0.05}
                               for (h, mu, ke, k, r), v in scan.items()]
    # IBM at a bistable point: two starts
    conds = []
    for k in (0.6, 0.8):
        for name, z0 in (("honest", HONEST_START), ("corrupt", CORRUPT_START)):
            conds.append(({"variant": "V2", "rho": 0.1, "kappa": k, "start": name},
                          ibm_condition(cfg, "ibm_small", rho=0.1, variant="V2", kappa=k,
                                        x0=z0[:4] / z0[:4].sum(), y0=float(z0[4]),
                                        seed_offset=31 if name == "honest" else 37)))
    out["ibm_small"] = run_conditions(cfg, conds)
    return out


def _sweep_kappa(p, rho, kappas, kexp, t_burn, t_win, z_start=None, direction="updown"):
    """V2 kappa sweep continuing the state between steps. direction 'updown' is the
    pre-registered protocol (start honest at the lowest kappa, sweep up, then down);
    'down' starts at the highest kappa from z_start and sweeps down (post-hoc)."""
    def step(k, z):
        q = mf_point(p, "V2", rho, k, z0=z, t_burn=t_burn, t_win=t_win, kexp=kexp)
        return {"kappa": k, "ybar": q["ybar"], "A_y": q["A_y"], "attractor": q["attractor"]},             np.array(q["z_end"])
    if direction == "down":
        z = np.array(z_start)
        down = []
        for k in kappas[::-1]:
            r, z = step(k, z)
            down.append(r)
        return {"rho": rho, "kexp": kexp, "direction": "down", "down": down[::-1]}
    up, down = [], []
    z = HONEST_START.copy()
    for k in kappas:
        r, z = step(k, z)
        up.append(r)
    for k in kappas[::-1]:
        r, z = step(k, z)
        down.append(r)
    return {"rho": rho, "kexp": kexp, "direction": "updown", "up": up, "down": down[::-1]}


E5B_CASES = ((0.1, 2.0), (0.27, 2.0), (0.29, 4.0))


def e5b(cfg):
    """Targeted follow-up of the E5 scan, which found bistability only at kappa close to 1:
    two-start maps in (rho, kappa), pre-registered and post-hoc kappa sweeps, IBM two starts."""
    full = cfg["profile"] == "full"
    tb = 8000 if full else 2000
    out = {"maps": []}
    rhos = list(np.linspace(0.05, 0.6, 12 if full else 4))
    kaps = [0.8, 0.85, 0.9, 0.93, 0.95, 0.97, 0.98, 0.99, 0.995] if full else [0.9, 0.99]
    for h, ke in E5B_CASES:
        p = mf_params(cfg, h=h)
        tasks, keys = [], []
        for r in rhos:
            for k in kaps:
                for name, z0 in (("honest", HONEST_START), ("corrupt", CORRUPT_START)):
                    tasks.append((mf_point, dict(p=p, variant="V2", rho=float(r), kappa=float(k),
                                                 kexp=ke, z0=z0, t_burn=tb, t_win=tb)))
                    keys.append((r, k, name))
        res = parallel(tasks, cfg["n_jobs"])
        grid = {}
        for (r, k, name), q in zip(keys, res):
            grid.setdefault((r, k), {})[name] = q["ybar"]
        out["maps"].append({"h": h, "kexp": ke, "rows": [
            {"rho": float(r), "kappa": float(k), "honest": v["honest"], "corrupt": v["corrupt"],
             "bistable": abs(v["honest"] - v["corrupt"]) > 0.05} for (r, k), v in grid.items()]})
    sweep_k = list(np.r_[np.linspace(0.0, 0.9, 10), np.linspace(0.92, 0.995, 9 if full else 3)])
    tasks = []
    for h, ke in ((0.1, 2.0), (0.29, 4.0)):
        p = mf_params(cfg, h=h)
        for r in (0.2, 0.4):
            tasks.append((_sweep_kappa, dict(p=p, rho=r, kappas=sweep_k, kexp=ke, t_burn=tb,
                                             t_win=tb)))
            tasks.append((_sweep_kappa, dict(p=p, rho=r, kappas=[k for k in sweep_k if k >= 0.8],
                                             kexp=ke, t_burn=tb, t_win=tb,
                                             z_start=CORRUPT_START, direction="down")))
    sw = parallel(tasks, cfg["n_jobs"])
    labels = [(h, ke, r, d) for h, ke in ((0.1, 2.0), (0.29, 4.0)) for r in (0.2, 0.4)
              for d in ("updown", "down")]
    out["sweeps"] = [{"h": h, **q} for (h, ke, r, d), q in zip(labels, sw)]
    conds = []
    S = cfg["ibm_small"]
    for h, ke, k, r in ((0.1, 2.0, 0.99, 0.4), (0.29, 4.0, 0.95, 0.2)):
        for name, z0, off in (("honest", HONEST_START, 131), ("corrupt", CORRUPT_START, 137)):
            for size, M in (("small", 50), ("medium", 500)):
                setting = dict(S, M=M, N=M // 5)
                run = cfg["ibm_small_run"] if size == "small" else dict(cfg["ibm_small_run"],
                                                                         win=cfg["ibm_small_run"]["win"] // 5)
                p = params_from(cfg, h=h)
                tasks = [(ibm_replicate, dict(p=p, setting=setting, run=run,
                                              seed=cfg["seed"] + off + M + 7919 * q, rho=r,
                                              variant="V2", kappa=k, kexp=ke,
                                              x0=z0[:4] / z0[:4].sum(), y0=float(z0[4])))
                         for q in range(cfg["reps"])]
                conds.append(({"start": name, "h": h, "kexp": ke, "kappa": k, "rho": r,
                               "M": M, "N": M // 5}, tasks))
    out["ibm"] = run_conditions(cfg, conds)
    return out


# ---------------------------------------------------------------------------
# E3 time series and E4 (H2)
# ---------------------------------------------------------------------------

def e3(cfg):
    p = mf_params(cfg)
    out = {"meanfield": [], "ibm_small": []}
    for r in (0.0, 0.012, 0.02, 0.1):
        q = mf_point(p, "V0", r, t_burn=2000, t_win=3000, dt=0.5, keep_series=3000)
        out["meanfield"].append({"rho": r, "series": q["series"], "attractor": q["attractor"]})
    S = cfg["ibm_small"]
    for r in (0.0, 0.03, 0.3):
        q = ibm_replicate(params_from(cfg), S, {"burn": 0, "win": 3000, "rec_dt": 0.5},
                          cfg["seed"] + 3, rho=r, keep_series=6000)
        out["ibm_small"].append({"rho": r, "series": q["series"]})
    return out


def e4(cfg):
    G = cfg["grids"]
    out = {}
    conds = [({"rho": r}, ibm_condition(cfg, "ibm_small", rho=r, seed_offset=41))
             for r in G["ibm_rho"]]
    out["ibm_small"] = run_conditions(cfg, conds)
    conds = [({"rho": r}, ibm_condition(cfg, "ibm_large", rho=r, seed_offset=43))
             for r in G["ibm_rho"]]
    out["ibm_large"] = run_conditions(cfg, conds)
    # stationarity check (R3): doubled window at rho = 0.03, small setting
    run2 = dict(cfg["ibm_small_run"])
    run2["win"] = 2 * run2["win"]
    S = cfg["ibm_small"]
    tasks = [(ibm_replicate, dict(p=params_from(cfg), setting=S, run=run2,
                                  seed=cfg["seed"] + 41 + 7919 * k, rho=0.03))
             for k in range(cfg["reps"])]
    out["stationarity_rho0.03"] = summarize_reps(parallel(tasks, cfg["n_jobs"]))
    return out


# ---------------------------------------------------------------------------
# E6: V3 stability vs kappa and T_lag (H6)
# ---------------------------------------------------------------------------

def _honest_branch_v0(p):
    """Continue the stable honest equilibrium of V0 downward in rho from rho = 0.6."""
    def mk(r):
        return make_model(p, "V0", r)
    # start from the attractor reached by simulation (random-start root finding can miss it)
    z = np.array(mf_point(p, "V0", 0.6, z0=HONEST_START, t_burn=5000, t_win=10)["z_end"])
    u = an.refine_equilibrium(mk(0.6), z[[0, 1, 2, 4]])
    br = an.continue_equilibria(mk, u, 0.6, 0.0, 0.61, ds=1e-3, direction=-1)
    # keep the part before the first fold (the honest node branch)
    stop = br["fold_idx"][0] + 1 if br["fold_idx"] else len(br["lam"])
    return br["lam"][:stop], br["u"][:stop]


def _v3_stability(p, rho, kappas, lags, lam_b, u_b, n_cheb=40):
    order = np.argsort(lam_b)
    lam_s, u_s = lam_b[order], u_b[order]
    rows = []
    for k in kappas:
        r_eff = rho * (1 - k)
        if r_eff < lam_s[0] or r_eff > lam_s[-1]:
            rows.append({"kappa": k, "exists": False})
            continue
        guess = np.array([np.interp(r_eff, lam_s, u_s[:, j]) for j in range(4)])
        m = make_model(p, "V3", rho, k)
        u = an.refine_equilibrium(make_model(p, "V1", rho, k), guess)
        if u is None:
            rows.append({"kappa": k, "exists": False})
            continue
        J0, J1 = an.jacobian(m, u, delayed=True)
        J1m = np.zeros((4, 4))
        J1m[:, 3] = J1[:, 0]
        v1_lead = float(np.max(np.linalg.eigvals(J0 + J1m).real))
        leads = []
        for L in lags:
            ev = an.dde_char_roots(J0, J1m, L, n=n_cheb)
            leads.append(float(ev[0].real))
        rows.append({"kappa": k, "exists": True, "y_eq": float(u[3]), "v1_lead": v1_lead,
                     "v3_lead": leads, "u": u.tolist()})
    return {"rho": rho, "lags": list(lags), "rows": rows}


def e6(cfg):
    p = mf_params(cfg)
    lam_b, u_b = _honest_branch_v0(p)
    nk, nl = cfg["grids"]["e6_kappa_n"], cfg["grids"]["e6_lag_n"]
    kappas = list(np.linspace(0, 0.95, nk))
    out = {"stability": []}
    for rho in (0.05, 0.1, 0.2):
        lags = list(np.r_[0.0, np.geomspace(0.5, 400, nl - 1)])
        out["stability"].append(_v3_stability(p, rho, kappas, lags, lam_b, u_b))
    # convergence check of the collocation (n = 80) at a few points
    chk = _v3_stability(p, 0.1, kappas[::max(1, nk // 4)], [1.0, 10.0, 100.0], lam_b, u_b,
                        n_cheb=80)
    out["collocation_check_n80"] = chk
    # DDE simulations at selected points (perturbed honest equilibrium)
    kw = dict(t_burn=cfg["ode"]["t_burn"], t_win=cfg["ode"]["t_win"], dt=0.5)
    tasks = []
    labels = []
    for rho in (0.05, 0.1):
        for k in (0.3, 0.6, 0.8):
            for L in (None, 50.0, 200.0):
                tasks.append((mf_point, dict(p=p, variant="V3", rho=rho, kappa=k,
                                             z0=HONEST_START, T_lag=L, **kw)))
                labels.append({"rho": rho, "kappa": k, "T_lag": (1 / rho) if L is None else L})
    res = parallel(tasks, cfg["n_jobs"])
    out["dde_sims"] = [{**lab, **{q: v[q] for q in ("ybar", "A_y", "attractor", "Cbar")}}
                       for lab, v in zip(labels, res)]
    return out


SECTIONS = {"bif": bif, "e1": e1, "e2": e2, "e3": e3, "e4": e4, "e5": e5, "e5b": e5b,
            "e6": e6}


def main(profile, sections):
    cfg = load_config(profile)
    t0 = time.time()
    for s in sections:
        t1 = time.time()
        data = SECTIONS[s](cfg)
        data["runtime_s"] = time.time() - t1
        path = save_result(f"ext_{s}", data, cfg)
        print(f"ext_{s}: {time.time() - t1:.1f} s -> {path}", flush=True)
    print(f"total {time.time() - t0:.1f} s")


if __name__ == "__main__":
    prof = sys.argv[1] if len(sys.argv) > 1 else "quick"
    secs = sys.argv[2:] or list(SECTIONS)
    main(prof, secs)
