"""Apply the pre-registered decision rules (METRICS.md Section 4) to the results.

Usage: python experiments/evaluate_hypotheses.py [quick|full]
Writes results/<profile>/hypotheses.json. Mean-field and IBM evidence are kept separate.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from src.utils import RESULTS, load_config, save_result


def L(name, profile):
    with open(os.path.join(RESULTS, profile, name + ".json")) as fh:
        return json.load(fh)["data"]


def nonoverlap(a, b):
    """True if two CI summaries {'lo','hi'} do not overlap."""
    return a["hi"] < b["lo"] or b["hi"] < a["lo"]


def h1(profile):
    bif = L("ext_bif", profile)
    e4 = L("ext_e4", profile)
    A = bif["attractors"]
    r = np.array([a["rho"] for a in A])
    yb = np.array([a["starts"][0]["ybar"] for a in A])
    amp = np.array([a["starts"][0]["A_y"] for a in A])
    # mean field: honesty increases (weakly) and amplitude decreases to 0 past rho_c
    dy = np.diff(yb)
    frac_up = float(np.mean(dy >= -1e-3))
    amp_zero_past = bool(np.all(amp[r > bif["rho_c"] * 1.01] < 1e-6))
    mf_honesty = bool(yb[-1] > yb[0] and frac_up >= 0.9)
    mf_damping = amp_zero_past and bool(amp[r > bif["rho_c"]].max() < amp[0])
    out = {"meanfield": {"ybar_rho0": float(yb[0]), "ybar_rho_max": float(yb[-1]),
                         "rho_max": float(r[-1]), "frac_steps_nondecreasing": frac_up,
                         "max_drop": float(-min(dy.min(), 0)), "amp_rho0": float(amp[0]),
                         "amplitude_zero_beyond_rho_c": amp_zero_past,
                         "honesty_up": mf_honesty, "damping": mf_damping}}
    for setting in ("ibm_small", "ibm_large"):
        cs = sorted(e4[setting], key=lambda c: c["rho"])
        s0, s1 = cs[0]["summary"], cs[-1]["summary"]
        out[setting] = {
            "rho_max": cs[-1]["rho"],
            "ybar_rho0": s0["ybar"], "ybar_rho_max": s1["ybar"],
            "episode_freq_rho0": s0["episode_freq_per_1000"],
            "episode_freq_rho_max": s1["episode_freq_per_1000"],
            "y_sd_rho0": s0["y_sd"], "y_sd_rho_max": s1["y_sd"],
            "honesty_up": bool(s1["ybar"]["lo"] > s0["ybar"]["hi"]),
            "damping": bool(s1["episode_freq_per_1000"]["hi"] < s0["episode_freq_per_1000"]["lo"]
                            or s1["y_sd"]["hi"] < s0["y_sd"]["lo"])}
    ok_mf = out["meanfield"]["honesty_up"] and out["meanfield"]["damping"]
    ok_ibm = out["ibm_small"]["honesty_up"] and out["ibm_small"]["damping"]
    out["outcome"] = "supported" if (ok_mf and ok_ibm) else (
        "mixed" if (ok_mf or ok_ibm or out["meanfield"]["honesty_up"]) else "not supported")
    out["note"] = ("Mean field: honesty is nearly flat for rho < rho_c (cycle persists, period "
                   "diverges) and rises steeply after the SNIC; cycles vanish at rho_c.")
    return out


def h2(profile):
    bif = L("ext_bif", profile)
    e4 = L("ext_e4", profile)
    A = [a for a in bif["attractors"] if a["starts"][0]["attractor"] != "equilibrium"]
    r = np.array([a["rho"] for a in A])
    x2 = np.array([a["starts"][0]["x2bar"] for a in A])
    dy = np.array([a["starts"][0]["depth_y"] for a in A])
    dc = np.array([a["starts"][0]["depth_C"] for a in A])
    mf = {"rho_range": [float(r.min()), float(r.max())], "x2bar_first": float(x2[0]),
          "x2bar_last_cycle": float(x2[-1]), "depth_y_first": float(dy[0]),
          "depth_y_last_cycle": float(dy[-1]), "depth_C_first": float(dc[0]),
          "depth_C_last_cycle": float(dc[-1]),
          "vigilance_declines": bool(x2[-1] < x2[0]),
          "deeper_y": bool(dy[-1] > dy[0] + 1e-3), "deeper_C": bool(dc[-1] < dc[0] - 1e-3)}
    out = {"meanfield": mf}
    deeper_any = mf["deeper_y"] or mf["deeper_C"]
    for setting in ("ibm_small", "ibm_large"):
        cs = sorted(e4[setting], key=lambda c: c["rho"])
        s0 = cs[0]["summary"]
        reps = s0["ybar"]["n"]
        rows = []
        for c in cs[1:]:
            s = c["summary"]
            has_ep = s["depth_C"]["n"] >= reps / 2
            rows.append({"rho": c["rho"], "has_episodes": bool(has_ep),
                         "x2_lower": bool(s["x2bar"]["hi"] < s0["x2bar"]["lo"]),
                         "deeper_y": bool(has_ep and s["depth_y"]["lo"] > s0["depth_y"]["hi"]),
                         "deeper_C": bool(has_ep and s["depth_C"]["hi"] < s0["depth_C"]["lo"]),
                         "shallower_C": bool(has_ep and s["depth_C"]["lo"] > s0["depth_C"]["hi"]),
                         "depth_C": s["depth_C"], "depth_y": s["depth_y"], "x2bar": s["x2bar"],
                         "recovery_time": s["recovery_time"]})
        out[setting] = {"rho0": {"depth_C": s0["depth_C"], "depth_y": s0["depth_y"],
                                 "x2bar": s0["x2bar"], "recovery_time": s0["recovery_time"]},
                        "rows": rows,
                        "vigilance_declines": any(q["x2_lower"] for q in rows),
                        "deeper_any": any(q["deeper_y"] or q["deeper_C"] for q in rows),
                        "shallower_any": any(q["shallower_C"] for q in rows)}
        deeper_any = deeper_any or out[setting]["deeper_any"]
    vig = mf["vigilance_declines"] and out["ibm_small"]["vigilance_declines"]
    if vig and deeper_any and (out["ibm_small"]["deeper_any"] and (mf["deeper_y"] or mf["deeper_C"])):
        res = "supported"
    elif vig and deeper_any:
        res = "mixed"
    else:
        res = "not supported"
    out["outcome"] = res
    out["note"] = ("Vigilance (PC) declines with rotation as predicted, but the remaining "
                   "episodes are not deeper by the pre-registered measures unless flagged above.")
    return out


def h3(profile):
    e2 = L("ext_e2", profile)
    out = {}
    for var in ("V1", "V2", "V3"):
        rows = [r for r in e2[f"meanfield_{var}"] if r["start"] == 0]
        rhos = sorted(set(r["rho"] for r in rows if r["rho"] > 0))
        dec = 0
        tot = 0
        for rho in rhos:
            ks = sorted([r for r in rows if r["rho"] == rho], key=lambda r: r["kappa"])
            yb = np.array([r["ybar"] for r in ks])
            tot += 1
            dec += int(yb[-1] < yb[0] - 1e-3 and np.all(np.diff(yb) <= 5e-3))
        out[f"meanfield_{var}"] = {"rho_values_decreasing": dec, "rho_values": tot}
    ib = e2["ibm_small"]
    eq = []
    for c in [c for c in ib if c["variant"] == "V1"]:
        m = [d for d in ib if d["variant"] == "V0eff" and d["rho"] == c["rho"]
             and d["kappa"] == c["kappa"]][0]
        a = np.array([q["ybar"] for q in c["per_rep"]])
        b = np.array([q["ybar"] for q in m["per_rep"]])
        rng = np.random.default_rng(1)
        diffs = [rng.choice(a, len(a)).mean() - rng.choice(b, len(b)).mean() for _ in range(20000)]
        lo, hi = np.quantile(diffs, [0.025, 0.975])
        eq.append({"rho": c["rho"], "kappa": c["kappa"], "diff": float(a.mean() - b.mean()),
                   "lo": float(lo), "hi": float(hi), "contains_0": bool(lo <= 0 <= hi),
                   "diffs": diffs})
    # post-hoc multiplicity check (not pre-registered): Bonferroni-adjusted intervals
    m = len(eq)
    for e in eq:
        blo, bhi = np.quantile(e.pop("diffs"), [0.025 / m, 1 - 0.025 / m])
        e["bonf_lo"], e["bonf_hi"] = float(blo), float(bhi)
        e["bonf_contains_0"] = bool(blo <= 0 <= bhi)
    out["ibm_V1_vs_V0eff"] = eq
    out["ibm_equivalence_holds"] = all(e["contains_0"] for e in eq)
    out["ibm_equivalence_n_excluding_0"] = int(sum(not e["contains_0"] for e in eq))
    out["ibm_equivalence_n_tests"] = len(eq)
    out["ibm_equivalence_max_abs_diff"] = float(max(abs(e["diff"]) for e in eq))
    out["ibm_equivalence_bonferroni_holds"] = all(e["bonf_contains_0"] for e in eq)
    dec_ibm = {}
    for var in ("V1", "V2", "V3"):
        cnt, tot = 0, 0
        for rho in sorted(set(c["rho"] for c in ib if c["variant"] == var)):
            ks = sorted([c for c in ib if c["variant"] == var and c["rho"] == rho],
                        key=lambda c: c["kappa"])
            tot += 1
            cnt += int(ks[-1]["summary"]["ybar"]["hi"] < ks[0]["summary"]["ybar"]["lo"])
        dec_ibm[var] = {"rho_values_decreasing": cnt, "rho_values": tot}
    out["ibm_decreasing"] = dec_ibm
    all_mf = all(out[f"meanfield_{v}"]["rho_values_decreasing"] >= 1 for v in ("V1", "V2", "V3"))
    all_ibm = all(dec_ibm[v]["rho_values_decreasing"] == dec_ibm[v]["rho_values"]
                  for v in ("V1", "V2", "V3"))
    out["outcome"] = "supported" if (all_mf and all_ibm) else "mixed"
    out["equivalence_verdict_preregistered"] = ("holds" if out["ibm_equivalence_holds"]
                                                else "breaks")
    out["note"] = ("H3 itself (inheritance weakens rotation) is judged on the decrease of honesty "
                   "with kappa. The V1 = V0(rho_eff) equivalence is exact in mean field; in the IBM "
                   "it is judged by the pre-registered rule (all CIs contain 0) and, post hoc, "
                   "with Bonferroni-adjusted intervals.")
    return out


def h4(profile):
    e1 = L("ext_e1", profile)
    mf = e1["meanfield"]
    hs = sorted(set(r["h"] for r in mf))
    rhos = sorted(set(r["rho"] for r in mf if r["rho"] > 0))
    get = {(r["h"], r["rho"]): r for r in mf}
    res = {}
    for key in ("ybar", "Cbar"):
        inc = dec = tot = 0
        for rho in rhos:
            for h_a, h_b in zip(hs[:-1], hs[1:]):
                da = get[(h_a, rho)][key] - get[(h_a, 0.0)][key]
                db = get[(h_b, rho)][key] - get[(h_b, 0.0)][key]
                tot += 1
                if db > da + 1e-4:
                    inc += 1
                elif db < da - 1e-4:
                    dec += 1
        cls = "substitutes" if inc >= 0.75 * tot else ("complements" if dec >= 0.75 * tot
                                                        else "mixed")
        res[key] = {"increasing_pairs": inc, "decreasing_pairs": dec, "pairs": tot,
                    "class": cls}
    # restrict to the admissible region (Eqs. 1-4 hold: h < sqrt(f(f+B)) = 0.2828)
    adm = {}
    for key in ("ybar", "Cbar"):
        inc = dec = tot = 0
        hs_a = [h for h in hs if h < np.sqrt(0.08)]
        for rho in rhos:
            for h_a, h_b in zip(hs_a[:-1], hs_a[1:]):
                da = get[(h_a, rho)][key] - get[(h_a, 0.0)][key]
                db = get[(h_b, rho)][key] - get[(h_b, 0.0)][key]
                tot += 1
                inc += int(db > da + 1e-4)
                dec += int(db < da - 1e-4)
        adm[key] = {"increasing_pairs": inc, "decreasing_pairs": dec, "pairs": tot,
                    "class": "substitutes" if inc >= 0.75 * tot else (
                        "complements" if dec >= 0.75 * tot else "mixed")}
    ib = e1["ibm_small"]
    ihs = sorted(set(c["h"] for c in ib))
    irhos = sorted(set(c["rho"] for c in ib if c["rho"] > 0))
    g = {(c["h"], c["rho"]): c["summary"]["ybar"]["mean"] for c in ib}
    inc = dec = tot = 0
    for rho in irhos:
        for h_a, h_b in zip(ihs[:-1], ihs[1:]):
            da = g[(h_a, rho)] - g[(h_a, 0.0)]
            db = g[(h_b, rho)] - g[(h_b, 0.0)]
            tot += 1
            inc += int(db > da + 1e-4)
            dec += int(db < da - 1e-4)
    ibm = {"increasing_pairs": inc, "decreasing_pairs": dec, "pairs": tot,
           "class": "substitutes" if inc >= 0.75 * tot else (
               "complements" if dec >= 0.75 * tot else "mixed"),
           "ybar_rho0_by_h": {str(h): g[(h, 0.0)] for h in ihs}}
    crit = [{"h": c["h"], "rho_c": (c["folds"][0] if c.get("folds") else None)}
            for c in e1["critical"]]
    out = {"meanfield_all_h": res, "meanfield_admissible_h": adm, "ibm_small": ibm,
           "rho_c_by_h": crit}
    mf_cls = adm["ybar"]["class"]
    if mf_cls == ibm["class"]:
        out["outcome"] = f"{mf_cls} (mean field and IBM agree)"
    else:
        out["outcome"] = f"mixed (mean field: {mf_cls}; IBM: {ibm['class']})"
    return out


def _open_region(rows):
    """Bistable points that have at least one bistable grid neighbour in rho and in kappa."""
    rs = sorted(set(r["rho"] for r in rows))
    ks = sorted(set(r["kappa"] for r in rows))
    B = {(r["rho"], r["kappa"]) for r in rows if r["bistable"]}
    n = 0
    for (r, k) in B:
        i, j = rs.index(r), ks.index(k)
        nb_r = any((rs[i + d], k) in B for d in (-1, 1) if 0 <= i + d < len(rs))
        nb_k = any((r, ks[j + d]) in B for d in (-1, 1) if 0 <= j + d < len(ks))
        n += int(nb_r and nb_k)
    return n


def h5(profile):
    e5 = L("ext_e5", profile)
    sc = e5["bistability_scan"]
    hy = e5["hysteresis"]
    maxgap = max(max(abs(u["ybar"] - d["ybar"]) for u, d in zip(h["up"], h["down"])) for h in hy)
    n_bi = int(sum(s["bistable"] for s in sc))
    out = {"default_scan": {"n_scan": len(sc), "n_bistable": n_bi,
                            "bistable_points": [s for s in sc if s["bistable"]],
                            "max_two_start_gap": float(max(abs(s["honest"]["ybar"]
                                                               - s["corrupt"]["ybar"]) for s in sc))},
           "preregistered_sweeps_max_gap": float(maxgap)}
    try:
        b = L("ext_e5b", profile)
    except FileNotFoundError:
        b = None
    open_region = False
    loop_prereg = maxgap > 0.05
    loop_posthoc = False
    if b is not None:
        maps = []
        for m in b["maps"]:
            nb = int(sum(r["bistable"] for r in m["rows"]))
            inner = _open_region(m["rows"])
            open_region = open_region or inner > 0
            ks = [r["kappa"] for r in m["rows"] if r["bistable"]]
            maps.append({"h": m["h"], "kexp": m["kexp"], "n_bistable": nb, "n": len(m["rows"]),
                         "n_interior": inner, "min_kappa_bistable": min(ks) if ks else None})
        out["targeted_maps"] = maps
        sw = []
        for q in b["sweeps"]:
            if q["direction"] == "updown":
                gap = max(abs(u["ybar"] - d["ybar"]) for u, d in zip(q["up"], q["down"]))
                loop_prereg = loop_prereg or gap > 0.05
                sw.append({"h": q["h"], "rho": q["rho"], "kexp": q["kexp"],
                           "protocol": "pre-registered up/down", "max_gap": gap})
            else:
                up = [x for x in b["sweeps"] if x["direction"] == "updown" and x["h"] == q["h"]
                      and x["rho"] == q["rho"]][0]["up"]
                upk = {u["kappa"]: u["ybar"] for u in up}
                gaps = [abs(d["ybar"] - upk[d["kappa"]]) for d in q["down"] if d["kappa"] in upk]
                low = [d["kappa"] for d in q["down"] if d["ybar"] < 0.5]
                loop_posthoc = loop_posthoc or (max(gaps) > 0.05 if gaps else False)
                sw.append({"h": q["h"], "rho": q["rho"], "kexp": q["kexp"],
                           "protocol": "post-hoc down from corrupt start",
                           "max_gap_vs_up": max(gaps) if gaps else None,
                           "corrupt_persists_down_to_kappa": min(low) if low else None})
        out["sweeps"] = sw
        ib = []
        for c in [c for c in b["ibm"] if c["start"] == "honest"]:
            d = [x for x in b["ibm"] if x["start"] == "corrupt" and x["h"] == c["h"]
                 and x["M"] == c["M"]][0]
            ib.append({"h": c["h"], "M": c["M"], "kappa": c["kappa"], "rho": c["rho"],
                       "honest_start": c["summary"]["ybar"], "corrupt_start": d["summary"]["ybar"],
                       "start_dependent": nonoverlap(c["summary"]["ybar"], d["summary"]["ybar"])})
        out["ibm_two_starts"] = ib
    out["bistable_open_region"] = bool(open_region)
    out["hysteresis_preregistered"] = bool(loop_prereg)
    out["hysteresis_posthoc"] = bool(loop_posthoc)
    if open_region and loop_prereg:
        res = "supported"
    elif open_region or loop_prereg or n_bi > 0:
        res = "mixed"
    else:
        res = "not supported"
    out["outcome"] = res
    out["note"] = ("Mean field: bistability only for kappa close to 1 with fast rotation; the "
                   "pre-registered sweep (from the honest state) shows no loop; a post-hoc sweep "
                   "down from the corrupt state shows one. IBM: no start dependence.")
    return out


def h6(profile):
    e6 = L("ext_e6", profile)
    rows = []
    unstable_v3_stable_v1 = 0
    total = 0
    maxlead = -np.inf
    for s in e6["stability"]:
        for r in s["rows"]:
            if not r["exists"]:
                continue
            for L_, lead in zip(s["lags"], r["v3_lead"]):
                total += 1
                maxlead = max(maxlead, lead)
                if r["kappa"] >= 0.5 and lead > 0 and r["v1_lead"] < 0:
                    unstable_v3_stable_v1 += 1
                    rows.append({"rho": s["rho"], "kappa": r["kappa"], "T_lag": L_, "lead": lead})
    chk = e6["collocation_check_n80"]
    sims = e6["dde_sims"]
    out = {"points_checked": total, "max_rightmost_real_part": float(maxlead),
           "n_destabilized_high_kappa": unstable_v3_stable_v1, "examples": rows[:10],
           "dde_sims": sims,
           "outcome": "supported" if unstable_v3_stable_v1 > 0 else "not supported"}
    out["collocation_n80_max_lead"] = float(max(max(r["v3_lead"]) for r in chk["rows"]
                                                if r["exists"]))
    return out


def main(profile):
    cfg = load_config(profile)
    out = {}
    for name, fn in (("H1", h1), ("H2", h2), ("H3", h3), ("H4", h4), ("H5", h5), ("H6", h6)):
        out[name] = fn(profile)
        print(name, out[name]["outcome"])
    save_result("hypotheses", out, cfg)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "quick")
