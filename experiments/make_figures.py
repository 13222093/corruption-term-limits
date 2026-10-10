"""Make all figures from results/<profile>/*.json (no simulation here).

Usage: python experiments/make_figures.py [quick|full]
Writes figures/ (full) or figures/quick/ (quick), PNG and vector PDF.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from src.plotting import (CAT, CORRUPT, DIV_BR, HONEST, INK, INK2, SEQ_BLUE, STRAT_COLORS,
                          STRAT_STYLES, panel_label, plt, save, setup)
from src.utils import RESULTS, fig_path

STRATS = ["OC", "PC", "OD", "PD"]


def L(name, profile):
    with open(os.path.join(RESULTS, profile, name + ".json")) as fh:
        return json.load(fh)


def ci_err(s):
    return [[s["mean"] - s["lo"]], [s["hi"] - s["mean"]]]


def errbar(ax, xs, summaries, key, color, label, marker="o", ls="-"):
    m = np.array([s[key]["mean"] for s in summaries], float)
    lo = np.array([s[key]["lo"] for s in summaries], float)
    hi = np.array([s[key]["hi"] for s in summaries], float)
    ax.plot(xs, m, ls, color=color, marker=marker, ms=4, label=label)
    ax.fill_between(xs, lo, hi, color=color, alpha=0.18, lw=0)


# ---------------------------------------------------------------------------
def fig01(profile):
    d = L("rep_b4_small", profile)["data"]
    t = np.array(d["t_steps"]) / 1e5
    x = np.array(d["x"])
    y = np.array(d["y"])
    fig, axs = plt.subplots(2, 1, figsize=(7.0, 4.6), sharex=True)
    for i, s in enumerate(STRATS):
        axs[0].plot(t, x[:, i], STRAT_STYLES[s], color=STRAT_COLORS[s], lw=1.1, label=s)
    axs[0].set_ylabel("Player frequency")
    axs[0].legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.2))
    axs[1].fill_between(t, 0, 1 - y, color=CORRUPT, lw=0, step="post", label="Corrupt")
    axs[1].fill_between(t, 1 - y, 1, color=HONEST, lw=0, step="post", label="Honest")
    axs[1].set_ylabel("Umpire fraction")
    axs[1].set_xlabel(r"Time (elementary steps, $10^5$)")
    axs[1].set_ylim(0, 1)
    axs[1].legend(ncol=2, loc="lower right")
    axs[1].grid(False)
    panel_label(axs[0], "A")
    panel_label(axs[1], "B")
    save(fig, fig_path("fig01_small_cycles", profile))


def fig02(profile):
    big = L("rep_b4_large", profile)["data"]
    f3 = L("rep_fig3", profile)["data"]
    sh = L("rep_shrinkage", profile)["data"]
    fig, axs = plt.subplots(2, 2, figsize=(8.0, 6.4))
    ax = axs[0, 0]
    t = np.array(big["t_steps"]) / 1e6
    xm = np.array(big["x_mean"])
    ym = np.array(big["y_mean"])
    ode = np.array(big["ode_z"])
    for i, s in enumerate(STRATS):
        ax.plot(t, xm[:, i], STRAT_STYLES[s], color=STRAT_COLORS[s], lw=1.2, label=s)
        ax.plot(t, ode[:, i], ":", color=STRAT_COLORS[s], lw=1.0)
    ax.plot(t, 1 - ym, color=CORRUPT, lw=1.6, label="corrupt umpires")
    ax.plot(t, 1 - ode[:, 4], ":", color=CORRUPT, lw=1.2)
    ax.set_xlabel(r"Time (elementary steps, $10^6$)")
    ax.set_ylabel("Frequency")
    ax.set_title(f"Large population: IBM mean of {big['reps']} runs (solid), mean field (dotted)",
                 fontsize=8)
    ax.legend(ncol=2, fontsize=7)
    panel_label(ax, "A")
    ax = axs[0, 1]
    for mu, col in zip(("0.0001", "0.02", "0.07"), (CAT[1], CAT[6], CAT[0])):
        o = f3[f"A2.0_mu{float(mu)}"]
        z = np.array(o.get("cycle_z", o["full_z"]))
        if o["attractor"] == "equilibrium":
            z = np.array(o["full_z"])  # show the damped approach
        ax.plot(z[:, 4], z[:, 0] + z[:, 1], color=col, lw=1.0,
                label=rf"$\mu=\nu={mu}$ ({o['attractor']})")
    ax.set_xlabel("Honest umpire fraction y")
    ax.set_ylabel(r"Cooperator frequency $x_1+x_2$")
    ax.set_title("Mean-field attractors from the Fig. 3 start (A = 2)", fontsize=8)
    ax.legend(fontsize=7, loc="lower left")
    panel_label(ax, "B")
    ax = axs[1, 0]
    for A, col in ((2.0, CAT[0]), (0.7, CAT[1])):
        pts = [q for q in sh["points"] if q["A"] == A]
        mus = [q["mu"] for q in pts]
        ax.semilogx(mus, [q["A_y"] for q in pts], "-o", color=col, ms=3, label=f"A = {A}")
        hm = sh["hopf"][f"A{A}"]["mu_hopf"]
        ax.axvline(hm, color=col, ls="--", lw=1)
        ax.text(hm, 0.9 if A == 2.0 else 0.75, f" Hopf {hm:.4f}", color=INK2, fontsize=7)
    ax.set_xlabel(r"Exploration rate $\mu=\nu$")
    ax.set_ylabel(r"Cycle amplitude of y, $\max\,y-\min\,y$")
    ax.legend()
    panel_label(ax, "C")
    ax = axs[1, 1]
    w = f3["fig3cd_window_mu0.02"]
    tt = np.array(w["t"])
    z = np.array(w["z"])
    for i, s in enumerate(STRATS):
        ax.plot(tt, z[:, i], STRAT_STYLES[s], color=STRAT_COLORS[s], lw=1.2, label=s)
    ax.plot(tt, z[:, 4], color=INK, lw=1.6, label="honest y")
    ax.set_xlabel("Time (model units)")
    ax.set_ylabel("Frequency")
    ax.set_title(r"Mean field, $\mu=\nu=0.02$: matches Lee et al. Fig. 3C, D", fontsize=8)
    ax.legend(ncol=3, fontsize=7, loc="upper center")
    ax.set_ylim(0, 1.15)
    panel_label(ax, "D")
    fig.tight_layout()
    save(fig, fig_path("fig02_damped_and_shrinkage", profile))


def fig03(profile):
    d = L("rep_b3", profile)["data"]
    m = L("rep_markov", profile)["data"]
    fig, ax = plt.subplots(figsize=(4.8, 3.4))
    mus = [e["mu"] for e in d["scan"]]
    r = [e["ratio"] for e in d["scan"]]
    ax.errorbar(mus, [q[0] for q in r], yerr=[[q[0] - q[1] for q in r], [q[2] - q[0] for q in r]],
                fmt="o-", color=CAT[0], capsize=3, label="IBM, mean of replicates (95% CI)")
    ax.axhline(m["ratio_N10_lam1"], color=INK, ls="--", lw=1.2,
               label=f"Markov chain, rare exploration ({m['ratio_N10_lam1']:.3f})")
    ax.scatter([0.001], [d["paper_sim_ratio"]], marker="*", s=90, color=CAT[1], zorder=5,
               label="Lee et al. simulation (2.15)")
    ax.set_xscale("log")
    ax.set_xlabel(r"Player exploration rate $\mu$ ($\nu = 5\mu$, so $M\mu = N\nu$)")
    ax.set_ylabel("Honest : corrupt time ratio")
    ax.legend(fontsize=7, loc="lower left")
    ax.invert_xaxis()
    save(fig, fig_path("fig03_hc_ratio", profile))


def fig04(profile):
    d = L("ext_bif", profile)["data"]
    fig, axs = plt.subplots(1, 3, figsize=(11.0, 3.6))
    ax = axs[0]
    br = d["branch"]
    rho = np.array(br["rho"])
    y = np.array(br["y"])
    st = np.array(br["stable"])
    for mask, ls, lab in ((st, "-", "stable equilibrium"), (~st, "--", "unstable equilibrium")):
        yy = np.where(mask, y, np.nan)
        ax.plot(rho, yy, ls, color=INK, lw=1.4, label=lab)
    A = d["attractors"]
    r_a = np.array([a["rho"] for a in A])
    s0 = [a["starts"][0] for a in A]
    cyc = np.array([q["attractor"] != "equilibrium" for q in s0])
    ax.fill_between(r_a, [q["y_absmin"] for q in s0], [q["y_absmax"] for q in s0],
                    where=cyc, color=CORRUPT, alpha=0.18, lw=0, label="limit-cycle range of y")
    ax.plot(r_a, [q["ybar"] for q in s0], "o", ms=2.5, color=CAT[0], label="time-averaged y")
    for f in d["folds"]:
        ax.axvline(f["rho"], color=INK2, lw=0.8, ls=":")
    ax.set_xlim(0, 0.2)
    ax.set_xlabel(r"Rotation rate $\rho$")
    ax.set_ylabel("Honest umpire fraction y")
    ax.legend(fontsize=7, loc="lower right")
    ax.set_title(rf"$\rho_c$ = {d['rho_c']:.4f} (SNIC), second fold {max(f['rho'] for f in d['folds']):.3f}",
                 fontsize=8)
    panel_label(ax, "A")
    ax = axs[1]
    sn = d["snic"]
    dd = np.array(sn["delta"])
    per = np.array(sn["period"], float)
    ax.loglog(dd, per, "o-", color=CAT[0], ms=4, label="period of the cycle")
    ref = per[np.isfinite(per)][0] * (dd / dd[0]) ** -0.5
    ax.loglog(dd, ref, "--", color=INK2, lw=1, label="slope -1/2")
    ax.set_xlabel(r"Distance to the fold, $\rho_c-\rho$")
    ax.set_ylabel("Period (model time)")
    ax.set_title(f"fitted slope {sn['loglog_slope']:.3f}", fontsize=8)
    ax.legend(fontsize=7)
    panel_label(ax, "B")
    ax = axs[2]
    for A_, col in ((2.0, CAT[0]), (0.7, CAT[1])):
        pts = [q for q in d["twopar"] if q["A"] == A_]
        mu = np.array([q["mu"] for q in pts])
        f1 = np.array([q["folds"][0] if len(q["folds"]) >= 1 else np.nan for q in pts])
        f2 = np.array([q["folds"][1] if len(q["folds"]) >= 2 else np.nan for q in pts])
        ap = np.array([q["rho_c_approx"] for q in pts])
        ax.plot(mu, f1, "-", color=col, lw=1.6, label=f"A = {A_}: fold creating honest state")
        ax.plot(mu, f2, "-.", color=col, lw=1.0, label=f"A = {A_}: second fold")
        ax.plot(mu, ap, ":", color=col, lw=1.2, label=f"A = {A_}: small-mu formula")
        for q in pts:
            for h in q["hopfs"]:
                ax.plot(q["mu"], h, "x", color=col, ms=5)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"Exploration rate $\mu=\nu$")
    ax.set_ylabel(r"Rotation rate $\rho$")
    ax.set_title("Two-parameter diagram (x: Hopf points)", fontsize=8)
    ax.legend(fontsize=6)
    panel_label(ax, "C")
    fig.tight_layout()
    save(fig, fig_path("fig04_bifurcation_rho", profile))


def _grid(rows, xkey, ykey, vkey):
    xs = sorted(set(r[xkey] for r in rows))
    ys = sorted(set(r[ykey] for r in rows))
    Z = np.full((len(ys), len(xs)), np.nan)
    for r in rows:
        Z[ys.index(r[ykey]), xs.index(r[xkey])] = r[vkey]
    return np.array(xs), np.array(ys), Z


def _edges(v):
    v = np.asarray(v, float)
    mid = (v[1:] + v[:-1]) / 2
    return np.r_[v[0] - (mid[0] - v[0]), mid, v[-1] + (v[-1] - mid[-1])]


def fig05(profile):
    d = L("ext_e1", profile)["data"]
    mf = d["meanfield"]
    fig, axs = plt.subplots(1, 3, figsize=(11.0, 3.6))
    xs, ys, Z = _grid(mf, "rho", "h", "ybar")
    im = axs[0].pcolormesh(_edges(xs), _edges(ys), Z, cmap=SEQ_BLUE, vmin=0, vmax=1)
    fig.colorbar(im, ax=axs[0], label="time-averaged honesty")
    xs, ys, Z = _grid(mf, "rho", "h", "A_y")
    im = axs[1].pcolormesh(_edges(xs), _edges(ys), Z, cmap=SEQ_BLUE, vmin=0, vmax=1)
    fig.colorbar(im, ax=axs[1], label=r"cycle amplitude of y")
    hs = [c["h"] for c in d["critical"]]
    # rho_c: the fold that creates the honest equilibrium (the smaller of two folds). When only
    # one fold remains (large h), it is the other fold and rho_c = 0 (the formula gives <= 0).
    def _rc(c):
        f = c.get("folds") or []
        if len(f) >= 2:
            return f[0]
        if c.get("approx") is not None and c["approx"] <= 0:
            return 0.0
        return np.nan
    rc = [_rc(c) for c in d["critical"]]
    ap = [max(c["approx"], 0.0) if c.get("approx") is not None else np.nan
          for c in d["critical"]]
    for ax in axs[:2]:
        ax.plot(rc, hs, "-", color=CORRUPT, lw=1.6, label=r"$\rho_c(h)$ (continuation)")
        ax.plot(ap, hs, ":", color=INK, lw=1.2, label="small-mu formula")
        ax.axhline(np.sqrt(0.2 * 0.4), color="#ffffff", ls="--", lw=1.0,
                   label=r"$h=\sqrt{f(f+B)}$ (Eq. 4 bound)")
        ax.set_xlabel(r"Rotation rate $\rho$")
        ax.set_ylabel("Information cost h")
        ax.set_xlim(_edges(xs)[0], _edges(xs)[-1])
        ax.grid(False)
    axs[0].legend(fontsize=6.5, loc="upper right", frameon=True, facecolor="#52514e",
                  labelcolor="#ffffff", framealpha=0.85)
    panel_label(axs[0], "A")
    panel_label(axs[1], "B")
    ax = axs[2]
    ib = d["ibm_small"]
    hvals = sorted(set(c["h"] for c in ib))
    for j, h in enumerate(hvals):
        cs = sorted([c for c in ib if c["h"] == h], key=lambda c: c["rho"])
        rr = [max(c["rho"], 1e-3) for c in cs]
        errbar(ax, rr, [c["summary"] for c in cs], "ybar", CAT[j % 8], f"h = {h}")
    ax.set_xscale("log")
    ax.set_xlabel(r"$\rho$ per generation ($\rho=0$ at $10^{-3}$)")
    ax.set_ylabel("time-averaged honesty")
    ax.set_title("IBM, small population (mean, 95% CI)", fontsize=8)
    ax.legend(fontsize=7)
    panel_label(ax, "C")
    fig.tight_layout()
    save(fig, fig_path("fig05_rho_h", profile))


def fig06(profile):
    d = L("ext_e2", profile)["data"]
    bif = L("ext_bif", profile)["data"]
    rho_c = bif["rho_c"]
    fig, axs = plt.subplots(2, 3, figsize=(11.0, 6.6))
    for j, var in enumerate(("V1", "V2", "V3")):
        rows = [r for r in d[f"meanfield_{var}"] if r["start"] == 0]
        xs, ys, Z = _grid(rows, "rho", "kappa", "ybar")
        ax = axs[0, j]
        im = ax.pcolormesh(_edges(xs), _edges(ys), Z, cmap=SEQ_BLUE, vmin=0.4, vmax=1)
        rr = np.linspace(max(rho_c * 1.0001, xs[1] * 0.5), xs[-1], 200)
        ax.plot(rr, 1 - rho_c / rr, "-", color=CORRUPT, lw=1.4,
                label=r"$\rho(1-\kappa)=\rho_c$")
        ax.set_xlim(_edges(xs)[0], _edges(xs)[-1])
        ax.set_ylim(_edges(ys)[0], _edges(ys)[-1])
        ax.set_title(f"{var} mean field: time-averaged honesty", fontsize=8)
        ax.set_xlabel(r"Rotation rate $\rho$")
        ax.set_ylabel(r"Inheritance weight $\kappa$")
        ax.grid(False)
        fig.colorbar(im, ax=ax)
        if j == 0:
            ax.legend(fontsize=7, loc="lower right")
        panel_label(ax, "ABC"[j])
    ib = d["ibm_small"]
    for j, r in enumerate(sorted(set(c["rho"] for c in ib if c["variant"] != "V0eff"))):
        ax = axs[1, j]
        for k, var in enumerate(("V1", "V2", "V3", "V0eff")):
            cs = sorted([c for c in ib if c["variant"] == var and c["rho"] == r],
                        key=lambda c: c["kappa"])
            lab = {"V0eff": r"V0 at $\rho(1-\kappa)$"}.get(var, var)
            errbar(ax, [c["kappa"] for c in cs], [c["summary"] for c in cs], "ybar",
                   CAT[k], lab, ls="-" if var != "V0eff" else ":")
        ax.set_title(rf"IBM small population, $\rho$ = {r} per generation", fontsize=8)
        ax.set_xlabel(r"Inheritance weight $\kappa$")
        ax.set_ylabel("time-averaged honesty")
        ax.legend(fontsize=7)
        panel_label(ax, "DEF"[j])
    fig.tight_layout()
    save(fig, fig_path("fig06_rho_kappa", profile))


def fig07(profile):
    bif = L("ext_bif", profile)["data"]
    e4 = L("ext_e4", profile)["data"]
    fig, axs = plt.subplots(2, 3, figsize=(11.0, 6.4))
    from matplotlib.ticker import MaxNLocator
    A = [a for a in bif["attractors"] if a["rho"] <= 0.03]
    r = np.array([a["rho"] for a in A])
    s0 = [a["starts"][0] for a in A]
    cyc = np.array([q["attractor"] != "equilibrium" for q in s0])
    ax = axs[0, 0]
    ax.plot(r, [q["x2bar"] for q in s0], "o-", ms=3, color=STRAT_COLORS["PC"], label="mean PC (vigilance)")
    ax.plot(r, [q["ybar"] for q in s0], "s-", ms=3, color=CAT[0], label="mean honesty y")
    ax.axvline(bif["rho_c"], color=INK2, ls=":", lw=1)
    ax.set_xlabel(r"Rotation rate $\rho$")
    ax.set_ylabel("Time average")
    ax.set_title("Mean field: vigilance falls as rotation rises", fontsize=8)
    ax.legend(fontsize=7)
    panel_label(ax, "A")
    ax = axs[0, 1]
    ax.plot(r[cyc], [q["depth_y"] for q, c in zip(s0, cyc) if c], "o-", ms=3, color=CORRUPT,
            label=r"peak corruption in episode, $1-\min\,y$")
    ax.plot(r[cyc], [q["depth_C"] for q, c in zip(s0, cyc) if c], "s-", ms=3,
            color=STRAT_COLORS["OC"], label=r"min cooperation in episode")
    ax.set_xlim(axs[0, 0].get_xlim())
    ax.axvline(bif["rho_c"], color=INK2, ls=":", lw=1)
    ax.set_xlabel(r"Rotation rate $\rho$")
    ax.set_ylabel("Episode depth measure")
    ax.set_title(r"Mean field: episode depth (cycles only, $\rho<\rho_c$)", fontsize=8)
    ax.legend(fontsize=7)
    panel_label(ax, "B")
    ax = axs[0, 2]
    per = [q["period"] if c else np.nan for q, c in zip(s0, cyc)]
    ax.plot(r, per, "o-", ms=3, color=CAT[6])
    ax.set_xlim(axs[0, 0].get_xlim())
    ax.axvline(bif["rho_c"], color=INK2, ls=":", lw=1)
    ax.set_xlabel(r"Rotation rate $\rho$")
    ax.set_ylabel("Cycle period (model time)")
    ax.set_title("Mean field: episodes become rarer", fontsize=8)
    panel_label(ax, "C")
    for a_ in axs[0]:
        a_.xaxis.set_major_locator(MaxNLocator(4))
    ib = sorted(e4["ibm_small"], key=lambda c: c["rho"])
    rr = [max(c["rho"], 1e-3) for c in ib]
    S = [c["summary"] for c in ib]
    ax = axs[1, 0]
    errbar(ax, rr, S, "x2bar", STRAT_COLORS["PC"], "mean PC (vigilance)")
    errbar(ax, rr, S, "ybar", CAT[0], "mean honesty y", marker="s")
    ax.set_xscale("log")
    ax.set_xlabel(r"$\rho$ per generation ($\rho=0$ at $10^{-3}$)")
    ax.set_ylabel("Time average")
    ax.set_title("IBM small population", fontsize=8)
    ax.legend(fontsize=7)
    panel_label(ax, "D")
    ax = axs[1, 1]
    errbar(ax, rr, S, "depth_C", STRAT_COLORS["OC"], "min cooperation in episode")
    errbar(ax, rr, S, "depth_y", CORRUPT, "peak corruption in episode", marker="s")
    ax.set_xscale("log")
    ax.set_xlabel(r"$\rho$ per generation")
    ax.set_ylabel("Episode depth measure")
    ax.set_title("IBM: depth of the remaining episodes", fontsize=8)
    ax.legend(fontsize=7)
    panel_label(ax, "E")
    ax = axs[1, 2]
    errbar(ax, rr, S, "episode_freq_per_1000", CAT[6], "episodes per 1000 generations")
    errbar(ax, rr, S, "recovery_time", CAT[1], "mean episode duration (generations)",
           marker="s")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"$\rho$ per generation")
    ax.set_title("IBM: frequency and duration of episodes", fontsize=8)
    ax.legend(fontsize=7)
    panel_label(ax, "F")
    fig.tight_layout()
    save(fig, fig_path("fig07_vigilance_h2", profile))


def fig08(profile):
    d = L("ext_e5", profile)["data"]
    b = L("ext_e5b", profile)["data"]
    fig, axs = plt.subplots(2, 3, figsize=(11.0, 6.6))
    ax = axs[0, 0]
    for j, h in enumerate(d["hysteresis"]):
        k = [u["kappa"] for u in h["up"]]
        ax.plot(k, [u["ybar"] for u in h["up"]], "-", color=CAT[j], lw=1.6,
                label=rf"$\rho$ = {h['rho']}: up")
        ax.plot(k, [u["ybar"] for u in h["down"]], "o", color=CAT[j], ms=3, mfc="none",
                label=rf"$\rho$ = {h['rho']}: down")
    ax.set_xlabel(r"Inheritance weight $\kappa$ (V2, k = 2, h = 0.1)")
    ax.set_ylabel("time-averaged honesty")
    ax.set_title("Pre-registered sweeps from the honest state: no loop", fontsize=8)
    ax.legend(fontsize=6.5, ncol=2)
    panel_label(ax, "A")
    for j, (h, ke) in enumerate(((0.1, 2.0), (0.29, 4.0))):
        ax = axs[0, 1 + j]
        m = [q for q in b["maps"] if q["h"] == h and q["kexp"] == ke][0]
        xs, ys = sorted(set(r["rho"] for r in m["rows"])), sorted(set(r["kappa"] for r in m["rows"]))
        Z = np.full((len(ys), len(xs)), np.nan)
        for r in m["rows"]:
            Z[ys.index(r["kappa"]), xs.index(r["rho"])] = abs(r["honest"] - r["corrupt"])
        im = ax.pcolormesh(_edges(xs), np.arange(len(ys) + 1), Z, cmap=SEQ_BLUE, vmin=0, vmax=1)
        ax.set_yticks(np.arange(len(ys)) + 0.5, [f"{k:g}" for k in ys])
        for i_, k_ in enumerate(ys):
            for j_, r_ in enumerate(xs):
                if Z[i_, j_] > 0.05:
                    ax.plot(r_, i_ + 0.5, ".", color="#ffffff", ms=3)
        ax.set_xlabel(r"Rotation rate $\rho$")
        ax.set_ylabel(r"Inheritance weight $\kappa$")
        ax.set_title(f"h = {h}, k = {ke:g}: two-start gap (dots: bistable)", fontsize=8)
        ax.grid(False)
        fig.colorbar(im, ax=ax)
        panel_label(ax, "BC"[j])
    ax = axs[1, 0]
    for j, (h, r) in enumerate(((0.1, 0.4), (0.29, 0.2))):
        upd = [q for q in b["sweeps"] if q["h"] == h and q["rho"] == r and q["direction"] == "updown"][0]
        dn = [q for q in b["sweeps"] if q["h"] == h and q["rho"] == r and q["direction"] == "down"][0]
        lab = f"h = {h}, k = {upd['kexp']:g}, " + r"$\rho$" + f" = {r}"
        ax.plot([u["kappa"] for u in upd["up"]], [u["ybar"] for u in upd["up"]], "-",
                color=CAT[j], lw=1.6, label=lab + ": up from honest")
        ax.plot([u["kappa"] for u in dn["down"]], [u["ybar"] for u in dn["down"]], "o--",
                color=CAT[j], ms=3, lw=1, label=lab + ": down from corrupt (post hoc)")
    ax.set_xlim(0.78, 1.0)
    ax.set_xlabel(r"Inheritance weight $\kappa$")
    ax.set_ylabel("time-averaged honesty")
    ax.set_title("Hysteresis appears only when starting corrupt", fontsize=8)
    ax.legend(fontsize=6)
    panel_label(ax, "D")
    ax = axs[1, 1]
    labels, means, errs, cols = [], [], [], []
    for c in sorted(b["ibm"], key=lambda c: (c["h"], c["N"], c["start"] != "honest")):
        labels.append(f"h={c['h']}\nN={c['N']}\n{c['start']}")
        s = c["summary"]["ybar"]
        means.append(s["mean"])
        errs.append([s["mean"] - s["lo"], s["hi"] - s["mean"]])
        cols.append(HONEST if c["start"] == "honest" else CORRUPT)
    xpos = np.arange(len(labels))
    ax.bar(xpos, means, color=cols, width=0.6)
    ax.errorbar(xpos, means, yerr=np.array(errs).T, fmt="none", ecolor=INK, capsize=3)
    ax.set_xticks(xpos, labels, fontsize=6)
    ax.set_ylim(0, 1)
    ax.set_ylabel("time-averaged honesty")
    ax.set_title("IBM at bistable mean-field points: no start dependence", fontsize=8)
    panel_label(ax, "E")
    ax = axs[1, 2]
    sc = d["bistability_scan"]
    diffs = np.array([abs(s["honest"]["ybar"] - s["corrupt"]["ybar"]) for s in sc])
    ax.hist(np.log10(np.maximum(diffs, 1e-12)), bins=30, color=CAT[0])
    ax.axvline(np.log10(0.05), color=CORRUPT, ls="--", lw=1.2, label="threshold 0.05")
    ax.set_xlabel(r"$\log_{10}|\bar y_{honest}-\bar y_{corrupt}|$")
    ax.set_ylabel("Number of parameter points")
    ax.set_title(f"Pre-registered scan: {int(sum(s['bistable'] for s in sc))} of {len(sc)} bistable",
                 fontsize=8)
    ax.legend(fontsize=7)
    panel_label(ax, "F")
    fig.tight_layout()
    save(fig, fig_path("fig08_conformist_hysteresis", profile))


def fig09(profile):
    d = L("ext_e6", profile)["data"]
    st = d["stability"]
    fig, axs = plt.subplots(1, len(st), figsize=(3.7 * len(st), 3.4))
    for j, s in enumerate(st):
        ax = axs[j]
        lags = np.array(s["lags"])
        rows = [r for r in s["rows"]]
        kap = np.array([r["kappa"] for r in rows])
        Z = np.full((len(kap), len(lags)), np.nan)
        for i, r in enumerate(rows):
            if r["exists"]:
                Z[i] = r["v3_lead"]
        lg = np.where(lags == 0, lags[1] / 2, lags)
        vmax = 0.12
        # blue = stable (negative real part), red = unstable
        im = ax.pcolormesh(_edges(np.log10(lg)), _edges(kap), Z, cmap=DIV_BR.reversed(),
                           vmin=-vmax, vmax=vmax)
        ax.axvline(np.log10(1 / s["rho"]), color=INK, ls="--", lw=1)
        ax.text(np.log10(1 / s["rho"]), kap[0], " one term (1/rho)", fontsize=7, va="bottom")
        noeq = ~np.array([r["exists"] for r in rows])
        if noeq.any():
            ax.axhline(kap[noeq][0] - (kap[1] - kap[0]) / 2, color=CORRUPT, lw=1.2)
            ax.text(np.log10(lg[0]), kap[noeq][0], "no honest equilibrium", fontsize=7,
                    color=CORRUPT, va="bottom")
        ax.set_xlabel(r"$\log_{10}$ delay $T_{lag}$ (0 plotted at left edge)")
        ax.set_ylabel(r"Inheritance weight $\kappa$")
        ax.set_title(rf"V3, $\rho$ = {s['rho']}: rightmost root real part", fontsize=8)
        ax.grid(False)
        fig.colorbar(im, ax=ax, label="Re(rightmost root)")
        panel_label(ax, "ABC"[j])
    fig.tight_layout()
    save(fig, fig_path("fig09_delay_stability", profile))


def fig10(profile):
    v = L("rep_validation", profile)["data"]
    fs = L("sens_finite", profile)["data"]
    fig, axs = plt.subplots(1, 2, figsize=(8.0, 3.4))
    ax = axs[0]
    M = np.array([p["M"] for p in v["points"]])
    rms = np.array([p["rms"][0] for p in v["points"]])
    lo = np.array([p["rms"][1] for p in v["points"]])
    hi = np.array([p["rms"][2] for p in v["points"]])
    ax.errorbar(M, rms, yerr=[rms - lo, hi - rms], fmt="o-", color=CAT[0], capsize=3,
                label="IBM vs exact mean field (RMS)")
    ax.loglog(M, rms[0] * (M / M[0]) ** -0.5, "--", color=INK2, lw=1, label=r"slope $-1/2$")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Players M (N = M/5)")
    ax.set_ylabel(f"RMS deviation over {int(v['T'])} generations")
    ax.legend(fontsize=7)
    panel_label(ax, "A")
    ax = axs[1]
    ib = fs["ibm"]
    for j, M_ in enumerate(sorted(set(c["M"] for c in ib))):
        cs = sorted([c for c in ib if c["M"] == M_], key=lambda c: c["rho"])
        errbar(ax, [max(c["rho"], 1e-3) for c in cs], [c["summary"] for c in cs], "ybar",
               CAT[j], f"M = {M_}, N = {M_ // 5}")
    ax.set_xscale("log")
    ax.set_xlabel(r"$\rho$ per generation ($\rho=0$ at $10^{-3}$)")
    ax.set_ylabel("time-averaged honesty")
    ax.set_title("Finite-size check (hard imitation)", fontsize=8)
    ax.legend(fontsize=7)
    panel_label(ax, "B")
    fig.tight_layout()
    save(fig, fig_path("fig10_validation_finite_size", profile))


def figS(profile):
    """Supplementary: time series (E3), sensitivity (R5), pulse vs continuous, p0, A = 0.7."""
    e3 = L("ext_e3", profile)["data"]
    fig, axs = plt.subplots(2, 4, figsize=(13.0, 5.6), sharey=True)
    for j, q in enumerate(e3["meanfield"]):
        ax = axs[0, j]
        t = np.array(q["series"]["t"])
        z = np.array(q["series"]["z"])
        for i, s in enumerate(STRATS):
            ax.plot(t, z[:, i], STRAT_STYLES[s], color=STRAT_COLORS[s], lw=1, label=s)
        ax.plot(t, z[:, 4], color=INK, lw=1.4, label="honest y")
        ax.set_title(rf"Mean field, $\rho$ = {q['rho']} ({q['attractor']})", fontsize=8)
        ax.set_xlabel("Time")
    axs[0, 0].legend(fontsize=6, ncol=2)
    for j, q in enumerate(e3["ibm_small"]):
        ax = axs[1, j]
        t = np.array(q["series"]["t"])
        x = np.array(q["series"]["x"])
        y = np.array(q["series"]["y"])
        ax.plot(t, x[:, 0] + x[:, 1], color=STRAT_COLORS["OC"], lw=0.8, label="cooperators")
        ax.plot(t, y, color=INK, lw=0.8, label="honest y")
        ax.set_title(rf"IBM small, $\rho$ = {q['rho']} per generation", fontsize=8)
        ax.set_xlabel("Generations")
    axs[1, 0].legend(fontsize=6)
    axs[1, 3].axis("off")
    fig.tight_layout()
    save(fig, fig_path("figS1_time_series", profile))

    oat = L("sens_oat", profile)["data"]
    base = [r for r in oat["meanfield"] if r["param"] == "base"][0]
    fig, axs = plt.subplots(1, 2, figsize=(9.0, 3.6))
    names = ["b", "c", "f", "B", "h", "A", "mu", "nu"]
    for k, (key, lab) in enumerate((("crit_folds", r"$\rho_c$ (fold creating honest state)"),
                                    ("gain", r"honesty gain at $\rho=0.05$"))):
        ax = axs[k]
        b0 = base[key][0] if key == "crit_folds" else base[key]
        for i, nme in enumerate(names):
            for fac, col in ((0.8, CAT[0]), (1.2, CAT[1])):
                r = [q for q in oat["meanfield"] if q["param"] == nme and q["value"] == fac][0]
                v = r[key][0] if key == "crit_folds" and r[key] else (
                    np.nan if key == "crit_folds" else r[key])
                ax.barh(i + (0.2 if fac > 1 else -0.2), (v - b0) / abs(b0), height=0.38,
                        color=col, label=f"{int(fac * 100)}% of base" if i == 0 else None,
                        hatch=None if r["admissible"] else "//", edgecolor=INK2 if not r["admissible"] else col)
        ax.set_yticks(range(len(names)), names)
        ax.axvline(0, color=INK, lw=0.8)
        ax.set_xlabel(f"relative change of {lab}")
        from matplotlib.patches import Patch
        ax.legend(handles=[Patch(color=CAT[0], label="80% of base"),
                           Patch(color=CAT[1], label="120% of base"),
                           Patch(facecolor="none", edgecolor=INK2, hatch="//",
                                 label="violates Eqs. 1-4")], fontsize=7)
        panel_label(ax, "AB"[k])
    fig.tight_layout()
    save(fig, fig_path("figS2_sensitivity", profile))

    pl = L("sens_pulse", profile)["data"]
    p0 = L("sens_p0", profile)["data"]
    alt = L("sens_altA", profile)["data"]
    ex = L("sens_explo", profile)["data"]
    fig, axs = plt.subplots(1, 3, figsize=(11.0, 3.4))
    ax = axs[0]
    for j, r in enumerate(sorted(set(q["rho"] for q in pl["meanfield"]))):
        qs = [q for q in pl["meanfield"] if q["rho"] == r]
        cont = [q for q in qs if q["tau"] is None][0]
        pul = sorted([q for q in qs if q["tau"] is not None], key=lambda q: q["tau"])
        ax.plot([q["tau"] for q in pul], [q["ybar"] for q in pul], "o-", color=CAT[j], ms=3,
                label=rf"pulses, $\rho$ = {r}")
        ax.axhline(cont["ybar"], color=CAT[j], ls=":", lw=1)
    ax.set_xlabel(r"Fraction replaced per pulse $\tau$ (period $T=\tau/\rho$)")
    ax.set_ylabel("time-averaged honesty (mean field)")
    ax.set_title("Pulses (markers) vs continuous (dotted)", fontsize=8)
    ax.legend(fontsize=7)
    panel_label(ax, "A")
    ax = axs[1]
    for j, (k, curve) in enumerate(p0["meanfield"].items()):
        ax.plot([q["rho"] for q in curve], [q["ybar"] for q in curve], "-", color=CAT[j],
                label=f"p0 = {k}")
    ax.plot([q["rho"] for q in alt["meanfield"]], [q["ybar"] for q in alt["meanfield"]], "--",
            color=CAT[4], label="A = 0.7 (p0 = 1)")
    ax.set_xlabel(r"Rotation rate $\rho$")
    ax.set_ylabel("time-averaged honesty (mean field)")
    ax.legend(fontsize=7)
    panel_label(ax, "B")
    ax = axs[2]
    for j, (mu, blk) in enumerate((k, v) for k, v in ex.items() if isinstance(v, dict)):
        cv = blk["meanfield"]
        ax.plot([q["rho"] for q in cv], [q["ybar"] for q in cv], "-", color=CAT[j],
                label=rf"$\mu=\nu$ = {mu}")
        if blk["critical"]["folds"]:
            ax.axvline(blk["critical"]["folds"][0], color=CAT[j], ls=":", lw=1)
    ax.set_xlabel(r"Rotation rate $\rho$")
    ax.set_ylabel("time-averaged honesty (mean field)")
    ax.set_title(r"Other exploration rates (dotted: $\rho_c$)", fontsize=8)
    ax.legend(fontsize=7)
    panel_label(ax, "C")
    fig.tight_layout()
    save(fig, fig_path("figS3_robustness", profile))


def main(profile):
    setup()
    for f in (fig01, fig02, fig03, fig04, fig05, fig06, fig07, fig08, fig09, fig10, figS):
        try:
            f(profile)
            print("ok", f.__name__)
        except FileNotFoundError as e:
            print("skip", f.__name__, "(missing results:", os.path.basename(str(e.filename)), ")")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "quick")
