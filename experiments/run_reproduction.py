"""Reproduction of Lee et al. (2019): benchmarks B1-B4 and validation of the IBM.

Usage: python experiments/run_reproduction.py [quick|full]
Writes results/<profile>/rep_*.json (with config hash and git commit).
"""
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import sympy as sp

from src import analysis as an
from src import rare_exploration as rx
from src.ibm import run_ibm
from src.metrics import bootstrap_ci, classify_attractor, cooperation, summarize
from src.params import FIG3_X0, Params
from src.replicator_mutator import Model, integrate, state
from src.runners import ibm_replicate, parallel, params_from
from src.utils import load_config, save_result


def b1_b2(cfg):
    """B1 (all corrupt) and B2 (all honest) from random starts, mu = nu = 0."""
    p = params_from(cfg, mu=0.0, nu=0.0)
    m = Model(p)
    rng = np.random.default_rng(cfg["seed"])
    target_b1 = np.array([0.0, (p.f + p.B - p.h) / (p.f + p.B), p.h / (p.f + p.B), 0.0])
    dev1, dev2, ends1 = [], [], []
    for _ in range(20):
        x0 = rng.dirichlet(np.ones(4))
        z1 = integrate(m, state(x0, 0.0), 40000).y[:, -1]
        z2 = integrate(m, state(x0, 1.0), 40000).y[:, -1]
        dev1.append(np.max(np.abs(z1[:4] - target_b1)))
        dev2.append(1.0 - z2[0])
        ends1.append(z1[:4].tolist())
    # printed weighting Q(y) = y Q_C + (1 - y) Q_H at y = 0
    mp = Model(p)
    mp.QH, mp.QC = mp.QC.copy(), mp.QH.copy()
    zp = integrate(mp, state([0.25] * 4, 0.0), 40000).y[:, -1]
    return {"b1_target": target_b1.tolist(), "b1_max_dev": float(max(dev1)),
            "b1_example_end": ends1[0], "b2_max_dev": float(max(dev2)),
            "printed_weighting_end_at_y0": zp[:4].tolist(), "n_starts": 20}


def _orbit(p, T, n_keep=4000):
    m = Model(p)
    t_eval = np.linspace(0, T, int(T * 2) + 1)
    sol = integrate(m, state(FIG3_X0, 1.0), T, t_eval=t_eval)
    late = sol.t >= T / 2
    t, Z = sol.t[late], sol.y[:, late].T
    c = classify_attractor(t, Z[:, 4])
    step = max(1, len(t) // n_keep)
    d8 = float(np.min(np.hypot(1 - Z[:, 2], Z[:, 4])))
    d9 = float(np.min(np.hypot(1 - Z[:, 3], Z[:, 4])))
    # period from successive downward crossings of y = 0.5 (robust for slow orbits)
    cr = np.where((Z[:-1, 4] >= 0.5) & (Z[1:, 4] < 0.5))[0]
    period_cross = float(np.mean(np.diff(t[cr]))) if len(cr) >= 2 else float("nan")
    if c["type"] != "equilibrium" and not np.isfinite(c["period"]):
        c["period"] = period_cross
    # one full-resolution cycle (or the last 200 time units at an equilibrium) for plotting
    span = 1.2 * c["period"] if np.isfinite(c["period"]) else 200.0
    one = t >= t[-1] - span
    cyc_step = max(1, int(one.sum() // 20000))
    return {"cycle_t": t[one][::cyc_step].tolist(), "cycle_z": Z[one][::cyc_step].tolist(),
            "attractor": c["type"], "period": c["period"], "period_cross": period_cross,
            "ybar": float(Z[:, 4].mean()),
            "max_x": Z[:, :4].max(axis=0).tolist(), "min_y": float(Z[:, 4].min()),
            "max_y": float(Z[:, 4].max()), "dist_state8": d8, "dist_state9": d9,
            "full_t": sol.t[::max(1, len(sol.t) // n_keep)].tolist(),
            "full_z": sol.y[:, ::max(1, len(sol.t) // n_keep)].T.tolist(),
            "late_t": t[::step].tolist(), "late_z": Z[::step].tolist()}


def fig3(cfg):
    """Fig. 3: orbits at mu = nu in {1e-4, 0.02, 0.07}, A in {2, 0.7}; Fig. 3C, D window."""
    out = {}
    tasks = []
    keys = []
    for A in (2.0, 0.7):
        for mu in (1e-4, 0.02, 0.07):
            T = 80000.0 if mu < 1e-3 else 8000.0
            tasks.append((_orbit, dict(p=params_from(cfg, A=A, mu=mu, nu=mu), T=T)))
            keys.append(f"A{A}_mu{mu}")
    res = parallel(tasks, cfg["n_jobs"])
    out = dict(zip(keys, res))
    # Fig. 3C, D analog: a 400-unit window of the mu = nu = 0.02 orbit (A = 2)
    p = params_from(cfg, mu=0.02, nu=0.02)
    sol = integrate(Model(p), state(FIG3_X0, 1.0), 6000, t_eval=np.arange(5000, 5400.01, 0.5))
    out["fig3cd_window_mu0.02"] = {"t": (sol.t - 5000).tolist(), "z": sol.y.T.tolist()}
    yth = an.invasion_thresholds(params_from(cfg))
    yth07 = an.invasion_thresholds(params_from(cfg, A=0.7))
    out["thresholds"] = {"A2": {"y_OD": yth[0], "y_PD": yth[1]},
                         "A0.7": {"y_OD": yth07[0], "y_PD": yth07[1]}}
    return out


def _shrink_point(p):
    T = 120000.0 if p.mu < 1e-3 else (40000.0 if p.mu < 0.01 else 12000.0)
    m = Model(p)
    t_eval = np.arange(T / 2, T + 1e-9, 0.5)
    sol = integrate(m, state(FIG3_X0, 1.0), T, t_eval=t_eval)
    y = sol.y[4]
    C = sol.y[0] + sol.y[1]
    c = classify_attractor(sol.t, y)
    cr = np.where((y[:-1] >= 0.5) & (y[1:] < 0.5))[0]
    if c["type"] != "equilibrium" and not np.isfinite(c["period"]) and len(cr) >= 2:
        c["period"] = float(np.mean(np.diff(sol.t[cr])))
    return {"mu": p.mu, "A": p.A, "A_y": float(y.max() - y.min()),
            "A_C": float(C.max() - C.min()), "ybar": float(y.mean()), "period": c["period"],
            "attractor": c["type"]}


def shrinkage(cfg):
    n = cfg["grids"]["fig3_mu_n"]
    mus = np.geomspace(1e-4, 0.08, n)
    tasks = [(_shrink_point, dict(p=params_from(cfg, A=A, mu=float(m), nu=float(m))))
             for A in (2.0, 0.7) for m in mus]
    pts = parallel(tasks, cfg["n_jobs"])
    hopf = {}
    for A in (2.0, 0.7):
        def mk(v, A=A):
            return Model(params_from(cfg, A=A, mu=v, nu=v))
        eq = an.find_equilibria(mk(0.08))
        u = [v for v in eq if np.all(an.full_state(v)[:4] > 1e-4)][0]
        h = an.locate_hopf(mk, 0.005, 0.08, u)
        hopf[f"A{A}"] = {"mu_hopf": h[0], "omega": h[2], "period_at_hopf": 2 * np.pi / h[2],
                         "eq": an.full_state(h[1]).tolist()}
    return {"points": pts, "hopf": hopf}


def markov(cfg):
    mu, lam, N = sp.symbols("mu lambda N", positive=True)
    p = params_from(cfg)
    Tp = rx.printed_T(mu, lam, N)
    Td = rx.derived_T(p, mu, lam, N)
    D = sp.simplify(Td - Tp)
    diffs = [[i + 1, j + 1, str(D[i, j])] for i in range(10) for j in range(10) if D[i, j] != 0]
    pis = rx.stationary_symbolic(Tp)
    ratio = sp.factor(sp.simplify(sum(pis[:5]) / sum(pis[5:])))
    pid = rx.stationary_symbolic(Td)
    ratio_d = sp.factor(sp.simplify(sum(pid[:5]) / sum(pid[5:])))
    out = {"ratio_printed": str(ratio), "ratio_derived": str(ratio_d),
           "derived_minus_printed": diffs,
           "events": [{k: (rx.STATE_NAMES[v] if k in ("frm", "to") else v) for k, v in e.items()}
                      for e in rx.derive_transitions(p)]}
    for Nv in (5, 10, 20):
        out[f"ratio_N{Nv}_lam1"] = float(ratio.subs({lam: 1, N: Nv}))
    S = cfg["ibm_small"]
    # finite-M variant: neutral player mutants fix with probability 1/M
    Tm = rx.derived_T(p, 1e-3, 1.0, S["N"], M=S["M"])
    out["ratio_finiteM_N10_M50"] = rx.hc_ratio(rx.stationary(Tm))
    pi = rx.stationary(rx.printed_T(1e-3, 1.0, S["N"]))
    out["stationary_N10_lam1"] = pi.tolist()
    # mean cycle length in generations at the IBM rates (mu_pop = M mu per generation)
    out["mu_pop_per_generation"] = S["M"] * S["mu"]
    return out


def b3(cfg):
    """IBM in the small setting: time-averaged H:C ratio vs the Markov chain prediction."""
    S = cfg["ibm_small"]
    p = params_from(cfg)
    b3c = cfg["b3"]
    reps = b3c["reps"]
    out = {"markov_ratio": float((19 * S["N"] + 87) / 109), "paper_sim_ratio": 2.15}
    scan = []
    for mu in b3c["mu_scan"]:
        scale = S["mu"] / mu
        gens = b3c["gens"] * scale
        setting = dict(S, mu=mu, nu=mu * S["nu"] / S["mu"])
        rec = 0.5 if scale <= 1 else 5.0
        run = {"burn": 5000 * scale, "win": gens, "rec_dt": rec}
        tasks = [(ibm_replicate, dict(p=p, setting=setting, run=run,
                                      seed=cfg["seed"] + 1000 * k + int(1e6 * mu)))
                 for k in range(reps)]
        res = parallel(tasks, cfg["n_jobs"])
        ratios = [r["ybar"] / (1 - r["ybar"]) for r in res]
        ybar = [r["ybar"] for r in res]
        # episodes per 1e5 elementary steps (1 generation = M + N steps)
        ep_steps = [r["episode_freq_per_1000"] / 1000 * 1e5 / (S["M"] + S["N"]) for r in res]
        entry = {"mu": mu, "nu": setting["nu"], "gens": gens, "reps": reps,
                 "ratio": bootstrap_ci(ratios), "ybar": bootstrap_ci(ybar),
                 "ratio_of_means": float(np.mean(ybar) / (1 - np.mean(ybar))),
                 "episodes_per_1e5_steps": bootstrap_ci(ep_steps),
                 "x_means": np.mean([[r["x1bar"], r["x2bar"], r["x3bar"], r["x4bar"]]
                                     for r in res], axis=0).tolist(),
                 "ratios": ratios}
        scan.append(entry)
    out["scan"] = scan
    # stationarity: double the window at the base rate
    run2 = {"burn": 5000, "win": 2 * b3c["gens"], "rec_dt": 0.5}
    res2 = parallel([(ibm_replicate, dict(p=p, setting=S, run=run2, seed=cfg["seed"] + 7 + k))
                     for k in range(reps)], cfg["n_jobs"])
    out["double_window_ratio"] = bootstrap_ci([r["ybar"] / (1 - r["ybar"]) for r in res2])
    # standard-error convergence check (R3): SE of ybar vs number of replicates
    yb = np.array([r["ybar"] for r in res2])
    out["se_vs_n"] = {int(n): float(np.std(yb[:n], ddof=1) / np.sqrt(n))
                      for n in (5, 10, 20, 30) if n <= len(yb)}
    return out


def b4_small(cfg):
    """Representative run for a Fig. 1A, B analog (window 2-3 x 10^5 elementary steps)."""
    S = cfg["ibm_small"]
    p = params_from(cfg, mu=S["mu"], nu=S["nu"])
    steps_per_gen = S["M"] + S["N"]
    t_end = 3e5 / steps_per_gen
    r = run_ibm(p, S["M"], S["N"], S["s"], t_end, 0.5, cfg["seed"] + 1,
                ibm_variant=S["ibm_variant"])
    w = r["t"] >= 2e5 / steps_per_gen
    return {"t_steps": (r["t"][w] * steps_per_gen).tolist(), "x": r["x"][w].tolist(),
            "y": r["y"][w].tolist(),
            "summary": summarize(r["t"][w], r["x"][w], r["y"][w], p, kind="ibm")}


def _large_run(p, L, T, seed):
    r = run_ibm(p, L["M"], L["N"], L["s"], T, 1.0, seed, ibm_variant=L["ibm_variant"])
    return {"t": r["t"].tolist(), "x": r["x"].tolist(), "y": r["y"].tolist()}


def b4_large(cfg):
    """Fig. 1C, D analog: damped oscillations in the large setting vs the exact mean field."""
    L = cfg["ibm_large"]
    p = params_from(cfg, mu=L["mu"], nu=L["nu"])
    steps_per_gen = L["M"] + L["N"]
    T = 5e6 / steps_per_gen
    reps = min(cfg["reps"], 10)
    runs = parallel([(_large_run, dict(p=p, L=L, T=T, seed=cfg["seed"] + 50 + k))
                     for k in range(reps)], cfg["n_jobs"])
    t = np.array(runs[0]["t"])
    X = np.array([r["x"] for r in runs])
    Y = np.array([r["y"] for r in runs])
    m = Model(p, kind="fermi", s=L["s"])
    sol = integrate(m, state([0, 0, 1, 0], 1.0), T, t_eval=t)
    eq = integrate(m, state([0, 0, 1, 0], 1.0), 30000.0).y[:, -1]
    u = np.array([eq[0], eq[1], eq[2], eq[4]])
    J = an.numeric_jacobian(m, u)
    ev = np.linalg.eigvals(J)
    late = t >= 400
    late_means = {"OC": bootstrap_ci(X[:, late, 0].mean(axis=1)),
                  "PC": bootstrap_ci(X[:, late, 1].mean(axis=1)),
                  "OD": bootstrap_ci(X[:, late, 2].mean(axis=1)),
                  "PD": bootstrap_ci(X[:, late, 3].mean(axis=1)),
                  "corrupt": bootstrap_ci(1 - Y[:, late].mean(axis=1))}
    return {"t_steps": (t * steps_per_gen).tolist(), "t_gen": t.tolist(),
            "x_rep0": X[0].tolist(), "y_rep0": Y[0].tolist(),
            "x_mean": X.mean(axis=0).tolist(), "y_mean": Y.mean(axis=0).tolist(),
            "ode_z": sol.y.T.tolist(), "fermi_equilibrium": eq.tolist(),
            "fermi_eigs": [[e.real, e.imag] for e in sorted(ev, key=lambda e: -e.real)],
            "late_means": late_means, "reps": reps,
            "paper_readoff": {"OC": 0.5, "PC": 0.2, "OD": 0.05, "PD": 0.22, "corrupt": 0.53}}


def _val_run(p, M, N, s, T, seed, ibm_variant="si"):
    r = run_ibm(p, M, N, s, T, 1.0, seed, ibm_variant=ibm_variant)
    return np.column_stack([r["x"], r["y"]])


def validation(cfg):
    """IBM vs its exact mean field for increasing population size (Fig. 10)."""
    L = cfg["ibm_large"]
    p = params_from(cfg, mu=L["mu"], nu=L["nu"])
    T = 100.0
    m = Model(p, kind="fermi", s=L["s"])
    t = np.arange(0, T + 1e-9, 1.0)
    sol = integrate(m, state([0, 0, 1, 0], 1.0), T, t_eval=t)
    Zode = sol.y.T
    out = []
    for M in (500, 2000, 8000, 32000):
        N = M // 5
        reps = 8
        Zs = parallel([(_val_run, dict(p=p, M=M, N=N, s=L["s"], T=T, seed=cfg["seed"] + M + k,
                                       ibm_variant=L["ibm_variant"]))
                       for k in range(reps)], cfg["n_jobs"])
        rms = [float(np.sqrt(np.mean((Z[:len(t)] - Zode) ** 2))) for Z in Zs]
        out.append({"M": M, "N": N, "rms": bootstrap_ci(rms), "rms_all": rms})
    return {"points": out, "T": T, "t": t.tolist(), "ode": Zode.tolist()}


# ---------------------------------------------------------------------------
# SI verification (branch si-verification): side-by-side variants, B3 investigation,
# comparisons with SI figures. See SI_EXTRACT.md and CHANGES_SI.md.
# ---------------------------------------------------------------------------

def _hc_defs(y):
    """Three definitions of a time-averaged honest-to-corrupt ratio from a recorded series y."""
    y = np.asarray(y, float)
    yb = y.mean()
    maj_h = np.mean(y > 0.5) + 0.5 * np.mean(y == 0.5)
    maj_c = np.mean(y < 0.5) + 0.5 * np.mean(y == 0.5)
    pure_h, pure_c = np.mean(y == 1.0), np.mean(y == 0.0)
    return {"ybar": float(yb), "ratio_means": float(yb / (1 - yb)),
            "ratio_majority": float(maj_h / maj_c) if maj_c > 0 else float("nan"),
            "ratio_pure": float(pure_h / pure_c) if pure_c > 0 else float("nan")}


def _b3_rep(p, S, burn, win, rec_dt, seed, diag=None, s=None, variant=None, x0=None):
    """One small-population replicate; returns the three ratio definitions on the window."""
    from src.ibm_diag import run_diag
    pp = p.with_(mu=S["mu"], nu=S["nu"])
    ss = S["s"] if s is None else s
    if diag:
        r = run_diag(pp, S["M"], S["N"], ss, burn + win, rec_dt, seed, x0=x0, **diag)
    else:
        r = run_ibm(pp, S["M"], S["N"], ss, burn + win, rec_dt, seed, x0=x0,
                    ibm_variant=variant or S.get("ibm_variant", "si"))
    w = r["t"] >= burn
    out = _hc_defs(r["y"][w])
    ep = summarize(r["t"][w], r["x"][w], r["y"][w], pp, kind="ibm")
    out["episodes_per_1e5_steps"] = ep["episode_freq_per_1000"] / 1000 * 1e5 / (S["M"] + S["N"])
    return out


def _summ(rows, key):
    return bootstrap_ci([r[key] for r in rows])


def si_compare(cfg):
    """B3 and B4 with ibm_variant = si and = reconstructed, same seeds (Step 3 of the SI task)."""
    S0 = cfg["ibm_small"]
    L0 = cfg["ibm_large"]
    p = params_from(cfg)
    b3c = cfg["b3"]
    out = {}
    for variant in ("si", "reconstructed"):
        S = dict(S0, ibm_variant=variant)
        tasks = [(_b3_rep, dict(p=p, S=S, burn=5000, win=b3c["gens"], rec_dt=0.5,
                                seed=cfg["seed"] + 1000 * k + int(1e6 * S["mu"])))
                 for k in range(b3c["reps"])]
        rows = parallel(tasks, cfg["n_jobs"])
        L = dict(L0, ibm_variant=variant)
        pl = params_from(cfg, mu=L["mu"], nu=L["nu"])
        T = 5e6 / (L["M"] + L["N"])
        reps = min(cfg["reps"], 10)
        runs = parallel([(_large_run, dict(p=pl, L=L, T=T, seed=cfg["seed"] + 50 + k))
                         for k in range(reps)], cfg["n_jobs"])
        tt = np.array(runs[0]["t"])
        X = np.array([r["x"] for r in runs])
        Y = np.array([r["y"] for r in runs])
        late = tt >= 400
        out[variant] = {
            "b3_ratio": _summ(rows, "ratio_means"), "b3_ratios": [r["ratio_means"] for r in rows],
            "b4_small_episodes_per_1e5_steps": _summ(rows, "episodes_per_1e5_steps"),
            "b4_large_late": {"OC": bootstrap_ci(X[:, late, 0].mean(axis=1)),
                              "PC": bootstrap_ci(X[:, late, 1].mean(axis=1)),
                              "OD": bootstrap_ci(X[:, late, 2].mean(axis=1)),
                              "PD": bootstrap_ci(X[:, late, 3].mean(axis=1)),
                              "corrupt": bootstrap_ci(1 - Y[:, late].mean(axis=1))}}
    out["identical"] = bool(out["si"]["b3_ratios"] == out["reconstructed"]["b3_ratios"]
                            and out["si"]["b4_large_late"] == out["reconstructed"]["b4_large_late"])
    return out


def b3_diag(cfg):
    """Investigation of the remaining B3 gap (published 2.15). Nothing here changes the default
    model; each check varies one plausible cause and reports the resulting ratio."""
    S = cfg["ibm_small"]
    p = params_from(cfg)
    reps = cfg["b3"]["reps"]
    gens = cfg["b3"]["gens"]
    seeds = [cfg["seed"] + 1000 * k + int(1e6 * S["mu"]) for k in range(reps)]

    def batch(**kw):
        burn = kw.pop("burn", 5000)
        win = kw.pop("win", gens)
        rec = kw.pop("rec_dt", 0.5)
        n = kw.pop("n", reps)
        sd = kw.pop("seeds", seeds)
        return parallel([(_b3_rep, dict(p=p, S=S, burn=burn, win=win, rec_dt=rec, seed=sd[k],
                                        **kw)) for k in range(n)], cfg["n_jobs"])

    out = {"published": 2.15, "markov": float((19 * S["N"] + 87) / 109)}
    base = batch()
    out["baseline"] = {k: _summ(base, k) for k in ("ratio_means", "ratio_majority", "ratio_pure",
                                                   "ybar")}
    out["baseline_per_rep_ratio"] = [r["ratio_means"] for r in base]
    vals = np.array(out["baseline_per_rep_ratio"])
    out["baseline_per_rep_sd"] = float(vals.std(ddof=1))
    out["baseline_frac_ge_published"] = float(np.mean(vals >= 2.15))
    out["switches"] = {}
    for sw in ("explore_any", "role_any", "self_payoff", "pair_step"):
        rows = batch(diag={sw: True})
        out["switches"][sw] = _summ(rows, "ratio_means")
    out["selection"] = {}
    for s in (1e3, 10.0):
        rows = batch(s=s)
        out["selection"][str(s)] = _summ(rows, "ratio_means")
    rows = batch(burn=50000)
    out["burn_in_50000"] = _summ(rows, "ratio_means")
    rows = batch(x0=[1.0, 0.0, 0.0, 0.0])
    out["start_allOC"] = _summ(rows, "ratio_means")
    # run length: Fig. 1A window (1e5 steps) and SI Fig. 7 length (2.2e8 steps)
    steps_per_gen = S["M"] + S["N"]
    short_n = 300 if cfg["profile"] == "full" else 40
    short = batch(win=1e5 / steps_per_gen, n=short_n,
                  seeds=[cfg["seed"] + 77 + k for k in range(short_n)])
    sv = np.array([r["ratio_means"] for r in short if np.isfinite(r["ratio_means"])])
    out["short_runs_1e5_steps"] = {"n": int(len(sv)), "mean": float(sv.mean()),
                                   "sd": float(sv.std(ddof=1)),
                                   "q05": float(np.quantile(sv, 0.05)),
                                   "q95": float(np.quantile(sv, 0.95)),
                                   "frac_ge_published": float(np.mean(sv >= 2.15))}
    long_n = 10 if cfg["profile"] == "full" else 3
    long_win = (2.2e8 if cfg["profile"] == "full" else 2.2e7) / steps_per_gen
    longr = batch(win=long_win, rec_dt=5.0, n=long_n,
                  seeds=[cfg["seed"] + 991 + k for k in range(long_n)])
    lv = np.array([r["ratio_means"] for r in longr])
    out["long_runs"] = {"steps": long_win * steps_per_gen, "n": long_n, "values": lv.tolist(),
                        "mean": float(lv.mean()), "sd": float(lv.std(ddof=1)),
                        "frac_ge_published": float(np.mean(lv >= 2.15))}
    return out


def _hyst(v, hi, lo):
    state, n = None, 0
    for a in v:
        if a > hi:
            if state == "low":
                n += 1
            state = "high"
        elif a < lo:
            state = "low"
    return n


def _fig8_count(p, M, s, seed, ibm_variant):
    """Cycles in 5e6 elementary steps, counted as for the digitized SI Fig. 8."""
    N = M // 5
    pp = p.with_(mu=0.01, nu=0.05)
    T = 5e6 / (M + N)
    r = run_ibm(pp, M, N, s, T, 0.5, seed, ibm_variant=ibm_variant)
    x = r["x"]
    if s >= 10:
        return _hyst(x[:, 3], 0.35, 0.08)
    return _hyst(x[:, 0], 0.7, 0.3)


def _period_at(p):
    T = 40000.0 if p.mu < 0.005 else 12000.0
    m = Model(p)
    sol = integrate(m, state(FIG3_X0, 1.0), T, t_eval=np.arange(T / 2, T + 1e-9, 0.25))
    c = classify_attractor(sol.t, sol.y[4])
    return c["period"] if c["type"] != "equilibrium" else float("nan")


def si_checks(cfg):
    """Our model against SI Fig. 8 (IBM cycle counts), SI Fig. 9B (mean-field periods), and the
    cost-free (h = 0) Markov-chain closed form of SI p.3 (IBM simulation)."""
    import json
    from src.utils import RESULTS
    with open(os.path.join(RESULTS, cfg["profile"], "si_digitized.json")) as fh:
        dig = json.load(fh)["data"]
    p = params_from(cfg)
    reps = 4 if cfg["profile"] == "full" else 2
    out = {"fig8": {}}
    keys = list(dig["fig8"])
    tasks = []
    for k in keys:
        d = dig["fig8"][k]
        for r in range(reps):
            tasks.append((_fig8_count, dict(p=p, M=d["M"], s=d["s"],
                                            seed=cfg["seed"] + 313 * r + d["M"] + int(d["s"]),
                                            ibm_variant=cfg["ibm_variant"])))
    res = parallel(tasks, cfg["n_jobs"])
    for i, k in enumerate(keys):
        ours = res[i * reps:(i + 1) * reps]
        out["fig8"][k] = {**dig["fig8"][k], "ours": ours, "ours_mean": float(np.mean(ours)),
                          "rel_diff": float(np.mean(ours) / dig["fig8"][k]["cycles"] - 1)}
    pts = dig["fig9b_label_points"]
    per = parallel([(_period_at, dict(p=params_from(cfg, h=q["h"], mu=q["mu"], nu=q["mu"])))
                    for q in pts], cfg["n_jobs"])
    out["fig9b"] = [{**q, "ours": pr, "rel_diff": (pr / q["label_period"] - 1)
                     if np.isfinite(pr) else None} for q, pr in zip(pts, per)]
    # h = 0: IBM vs SI closed form 14 + 8N + 12M : 25 (lambda = 1)
    S = cfg["ibm_small"]
    pred = (14 + 8 * S["N"] + 12 * S["M"]) / 25
    p0 = params_from(cfg, h=0.0)
    h0 = {}
    for mu in cfg["b3"]["mu_scan"][:2]:
        scale = S["mu"] / mu
        setting = dict(S, mu=mu, nu=mu * S["nu"] / S["mu"])
        rows = parallel([(_b3_rep, dict(p=p0, S=setting, burn=5000 * scale,
                                        win=cfg["b3"]["gens"] * scale,
                                        rec_dt=0.5 if scale <= 1 else 5.0,
                                        seed=cfg["seed"] + 4242 + k))
                         for k in range(cfg["b3"]["reps"])], cfg["n_jobs"])
        h0[str(mu)] = _summ(rows, "ratio_means")
    out["h0"] = {"markov_prediction": pred, "ibm": h0}
    return out


SECTIONS = [("rep_b1b2", b1_b2), ("rep_fig3", fig3), ("rep_shrinkage", shrinkage),
            ("rep_markov", markov), ("rep_b3", b3), ("rep_b4_small", b4_small),
            ("rep_b4_large", b4_large), ("rep_validation", validation),
            ("rep_si_compare", si_compare), ("rep_b3_diag", b3_diag),
            ("rep_si_checks", si_checks)]


def main(profile, only=None):
    cfg = load_config(profile)
    t0 = time.time()
    for name, fn in SECTIONS:
        if only and name not in only:
            continue
        t1 = time.time()
        data = fn(cfg)
        data["runtime_s"] = time.time() - t1
        path = save_result(name, data, cfg)
        print(f"{name}: {time.time() - t1:.1f} s -> {path}", flush=True)
    print(f"total {time.time() - t0:.1f} s")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "quick", sys.argv[2:] or None)
