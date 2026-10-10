"""Generate paper/autogen_numbers.tex (LaTeX macros) and results/<profile>/numbers.md from the
results files. Every quantitative claim in the paper uses these macros (R6).

Usage: python experiments/make_numbers.py [full|quick]
"""
from __future__ import annotations

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from src.utils import ROOT, RESULTS, load_config

MACROS: list[tuple[str, str, str]] = []


def R(name, profile):
    with open(os.path.join(RESULTS, profile, name + ".json")) as fh:
        return json.load(fh)["data"]


def fmt(v, nd=3):
    if v is None or (isinstance(v, float) and not math.isfinite(v)):
        return "n/a"
    if isinstance(v, (int, np.integer)):
        return f"{int(v)}"
    return f"{v:.{nd}f}"


def sci(v, nd=1):
    if v == 0:
        return "0"
    e = int(math.floor(math.log10(abs(v))))
    m = v / 10 ** e
    return f"{m:.{nd}f}\\times 10^{{{e}}}"


def M(name, value, desc, nd=3, kind="f"):
    assert name.isalpha(), name
    if kind == "s":
        s = sci(value, nd)
    elif kind == "raw":
        s = str(value)
    elif kind == "pct":
        s = f"{100 * value:.{nd}f}"
    else:
        s = fmt(value, nd)
    MACROS.append((name, s, desc))


def ci(name, s, desc, nd=3):
    """s: [mean, lo, hi, n] or {'mean','lo','hi'}"""
    if isinstance(s, dict):
        m, lo, hi = s["mean"], s["lo"], s["hi"]
    else:
        m, lo, hi = s[0], s[1], s[2]
    M(name, m, desc, nd)
    M(name + "Lo", lo, desc + " (95% CI low)", nd)
    M(name + "Hi", hi, desc + " (95% CI high)", nd)


def build(profile):
    cfg = load_config(profile)
    M("Nreps", cfg["reps"], "IBM replicates per condition", kind="raw")
    M("MSmall", cfg["ibm_small"]["M"], "players, small setting", kind="raw")
    M("NSmall", cfg["ibm_small"]["N"], "umpires, small setting", kind="raw")
    M("WinSmall", int(cfg["ibm_small_run"]["win"]), "window, small IBM (generations)", kind="raw")
    M("BurnSmall", int(cfg["ibm_small_run"]["burn"]), "burn-in, small IBM", kind="raw")
    M("WinLarge", int(cfg["ibm_large_run"]["win"]), "window, large IBM", kind="raw")
    M("BurnLarge", int(cfg["ibm_large_run"]["burn"]), "burn-in, large IBM", kind="raw")
    M("TBurnMF", int(cfg["ode"]["t_burn"]), "mean-field burn-in", kind="raw")
    M("TWinMF", int(cfg["ode"]["t_win"]), "mean-field window", kind="raw")
    M("MuMF", cfg["ode"]["mu"], "mean-field exploration rate", nd=2)

    # ---- reproduction ----
    b = R("rep_b1b2", profile)
    M("BoneOD", b["b1_target"][2], "B1 target OD", 2)
    M("BonePC", b["b1_target"][1], "B1 target PC", 2)
    M("BoneDev", b["b1_max_dev"], "B1 max deviation", 1, "s")
    M("BtwoDev", b["b2_max_dev"], "B2 max deviation", 1, "s")
    M("BoneStarts", b["n_starts"], "random starts", kind="raw")
    M("PrintedOC", b["printed_weighting_end_at_y0"][0], "OC under printed weighting at y=0", 3)

    sh = R("rep_shrinkage", profile)
    M("HopfMuA", sh["hopf"]["A2.0"]["mu_hopf"], "Hopf in mu=nu, A=2", 4)
    M("HopfMuB", sh["hopf"]["A0.7"]["mu_hopf"], "Hopf in mu=nu, A=0.7", 4)
    M("HopfPerA", sh["hopf"]["A2.0"]["period_at_hopf"], "period at Hopf, A=2", 1)

    f3 = R("rep_fig3", profile)
    o = f3["A2.0_mu0.0001"]
    M("PerSlow", o["period"], "period mu=1e-4, A=2", 0)
    M("SlowOCmax", o["max_x"][0], "max OC mu=1e-4", 3)
    M("SlowPDmax", o["max_x"][3], "max PD mu=1e-4", 3)
    v = f3["A2.0_mu0.02"]
    M("PerViolet", v["period"], "period mu=0.02", 1)
    for i, s in enumerate(("OC", "PC", "OD", "PD")):
        M(f"Violet{s}", v["max_x"][i], f"max {s}, mu=0.02", 3)
    M("VioletYmin", v["min_y"], "min honest, mu=0.02", 3)
    M("SlowDistNine", o["dist_state9"], "min distance to state 9, A=2", 3)
    M("SlowDistEight", o["dist_state8"], "min distance to state 8, A=2", 3)
    w = f3["A0.7_mu0.0001"]
    M("SlowBDistEight", w["dist_state8"], "min distance to state 8, A=0.7", 3)
    M("SlowBDistNine", w["dist_state9"], "min distance to state 9, A=0.7", 3)
    M("PerSlowB", w["period"], "period mu=1e-4, A=0.7", 0)
    th = f3["thresholds"]
    M("yODA", th["A2"]["y_OD"], "y_OD at A=2", 3)
    M("yPD", th["A2"]["y_PD"], "y_PD", 3)
    M("yODB", th["A0.7"]["y_OD"], "y_OD at A=0.7", 3)

    mk = R("rep_markov", profile)
    M("MarkovRatio", mk["ratio_N10_lam1"], "Markov H:C at N=10", 3)
    M("MarkovRatioFinM", mk["ratio_finiteM_N10_M50"], "Markov with 1/M neutral player fixation", 3)
    M("MarkovNdiff", len(mk["derived_minus_printed"]), "number of differing entries", kind="raw")

    b3 = R("rep_b3", profile)
    sc = {e["mu"]: e for e in b3["scan"]}
    ci("BthreeRatio", sc[0.001]["ratio"], "IBM H:C at mu=1e-3")
    ci("BthreeRatioB", sc[0.0003]["ratio"], "IBM H:C at mu=3e-4")
    if 0.0001 in sc:
        ci("BthreeRatioC", sc[0.0001]["ratio"], "IBM H:C at mu=1e-4")
    ci("BthreeDouble", b3["double_window_ratio"], "H:C with doubled window")
    ci("EpisodesSteps", sc[0.001]["episodes_per_1e5_steps"], "episodes per 1e5 steps", 1)
    M("BthreeGens", int(sc[0.001]["gens"]), "generations per replicate", kind="raw")
    M("PaperRatio", b3["paper_sim_ratio"], "paper simulated ratio", 2)
    M("BthreeSE", b3["se_vs_n"]["30"] if "30" in b3["se_vs_n"] else list(b3["se_vs_n"].values())[-1],
      "SE of ybar at 30 reps (B3)", 4)

    bl = R("rep_b4_large", profile)
    for s in ("OC", "PC", "OD", "PD", "corrupt"):
        ci(f"Bfour{s.capitalize() if s == 'corrupt' else s}", bl["late_means"][s],
           f"large IBM late mean {s}")
    M("FermiCorrupt", 1 - bl["fermi_equilibrium"][4], "Fermi mean-field corrupt fraction", 3)
    M("FermiRe", bl["fermi_eigs"][0][0], "leading eigenvalue real part", 4)
    M("FermiIm", abs(bl["fermi_eigs"][0][1]), "leading eigenvalue imaginary part", 4)
    M("FermiPer", 2 * math.pi / abs(bl["fermi_eigs"][0][1]), "damped oscillation period (gen)", 0)
    M("FermiDecay", -1 / bl["fermi_eigs"][0][0], "decay time (gen)", 0)
    M("LargeReps", bl["reps"], "large IBM replicates (B4)", kind="raw")

    val = R("rep_validation", profile)
    for p_, nm in zip(val["points"], ("A", "B", "C", "D")):
        M(f"ValM{nm}", p_["M"], "validation M", kind="raw")
        M(f"ValRms{nm}", p_["rms"][0], "validation RMS", 3)

    # ---- extension: bifurcation ----
    bif = R("ext_bif", profile)
    M("RhoC", bif["rho_c"], "critical rotation rate (fold, SNIC)", 4)
    M("RhoCApprox", bif["rho_c_approx"], "small-mu formula", 4)
    M("RhoCErr", abs(bif["rho_c_approx_rel_err"]), "relative error of formula (percent)", 1, "pct")
    M("RhoCy", bif["rho_c_approx_y"], "honesty at the fold (formula)", 3)
    folds = sorted(f["rho"] for f in bif["folds"])
    M("RhoFtwo", folds[-1], "second fold", 3)
    fold1 = [f for f in bif["folds"] if f["rho"] == folds[0]][0]
    M("FoldY", fold1["u"][4], "honest fraction at the fold", 3)
    M("FoldOC", fold1["u"][0], "OC at the fold", 3)
    M("FoldPC", fold1["u"][1], "PC at the fold", 3)
    M("SnicSlope", bif["snic"]["loglog_slope"], "log-log slope of period", 3)
    M("NHopfDefault", len(bif["hopfs"]), "Hopf points at default", kind="raw")
    A = bif["attractors"]
    a0 = A[0]["starts"][0]
    M("YbarZero", a0["ybar"], "mean honesty rho=0", 3)
    M("PCZero", a0["x2bar"], "mean PC rho=0", 3)
    M("PerZero", a0["period"], "period rho=0", 1)
    M("YminZero", a0["y_absmin"], "min y on cycle rho=0", 3)
    cyc = [a for a in A if a["starts"][0]["attractor"] != "equilibrium"]
    last = cyc[-1]
    M("RhoLastCycle", last["rho"], "largest rho with a cycle", 4)
    M("YbarLastCycle", last["starts"][0]["ybar"], "mean honesty just below rho_c", 3)
    M("PCLastCycle", last["starts"][0]["x2bar"], "mean PC just below rho_c", 3)
    M("DepthCZero", a0["depth_C"], "min cooperation in episode, rho=0", 3)
    M("DepthCLast", last["starts"][0]["depth_C"], "min cooperation in episode, near rho_c", 3)
    M("DepthYZero", a0["depth_y"], "peak corruption rho=0", 3)
    M("DepthYLast", last["starts"][0]["depth_y"], "peak corruption near rho_c", 3)
    eqs = [a for a in A if a["starts"][0]["attractor"] == "equilibrium"]
    firsteq = eqs[0]
    M("RhoFirstEq", firsteq["rho"], "first rho with equilibrium", 4)
    M("YbarFirstEq", firsteq["starts"][0]["ybar"], "honesty just above rho_c", 3)
    M("PCFirstEq", firsteq["starts"][0]["x2bar"], "PC just above rho_c", 3)
    for rr, nm in ((0.05, "Five"), (0.1, "Ten"), (0.2, "Twenty")):
        a = min(A, key=lambda q: abs(q["rho"] - rr))
        M(f"YbarRho{nm}", a["starts"][0]["ybar"], f"honesty at rho={rr}", 3)
        M(f"PCRho{nm}", a["starts"][0]["x2bar"], f"PC at rho={rr}", 3)
    # two-parameter: rho_c / mu ratios at the smallest mu, and largest mu with folds
    tp = bif["twopar"]
    for A_, nm in ((2.0, "A"), (0.7, "B")):
        pts = sorted([q for q in tp if q["A"] == A_], key=lambda q: q["mu"])
        q0 = pts[0]
        M(f"RhoCOverMu{nm}", q0["folds"][0] / q0["mu"], f"rho_c/mu at small mu, A={A_}", 2)
        withf = [q for q in pts if len(q["folds"]) == 2]
        M(f"MuMaxFold{nm}", withf[-1]["mu"], f"largest mu with two folds, A={A_}", 3)
        hops = [(q["mu"], h) for q in pts for h in q["hopfs"]]
        M(f"NHopfTwopar{nm}", len(hops), f"Hopf points in two-parameter scan, A={A_}", kind="raw")
        relerr = [abs(q["rho_c_approx"] - q["folds"][0]) / q["folds"][0] for q in pts
                  if len(q["folds"]) == 2 and q["mu"] <= 0.011]
        M(f"ApproxErrMax{nm}", max(relerr), f"max rel err of formula for mu<=0.011, A={A_}", 1,
          "pct")

    # ---- E1 ----
    e1 = R("ext_e1", profile)
    crit = {c["h"]: c for c in e1["critical"]}
    M("RhoCLowH", crit[0.02]["folds"][0], "rho_c at h=0.02", 4)
    M("RhoCHighH", crit[0.28]["folds"][0], "rho_c at h=0.28", 4)
    rcs = [(h, c["folds"][0]) for h, c in crit.items() if len(c.get("folds", [])) == 2]
    hmax = max(rcs, key=lambda q: q[1])
    M("RhoCMaxH", hmax[0], "h where rho_c is largest", 2)
    M("RhoCMax", hmax[1], "largest rho_c", 4)
    mf = {(r["h"], r["rho"]): r for r in e1["meanfield"]}
    M("YbarZeroLowH", mf[(0.02, 0.0)]["ybar"], "honesty rho=0 h=0.02", 3)
    M("YbarZeroHighH", mf[(0.28, 0.0)]["ybar"], "honesty rho=0 h=0.28", 3)
    M("GainLowH", mf[(0.02, 0.05)]["ybar"] - mf[(0.02, 0.0)]["ybar"], "gain at rho=0.05, h=0.02", 3)
    M("GainHighH", mf[(0.28, 0.05)]["ybar"] - mf[(0.28, 0.0)]["ybar"], "gain at rho=0.05, h=0.28",
      3)

    # ---- hypotheses ----
    hy = R("hypotheses", profile)
    h1 = hy["H1"]
    for setting, nm in (("ibm_small", "S"), ("ibm_large", "L")):
        ci(f"HoneY{nm}Zero", h1[setting]["ybar_rho0"], f"H1 {setting} ybar rho=0")
        ci(f"HoneY{nm}Max", h1[setting]["ybar_rho_max"], f"H1 {setting} ybar rho max")
        ci(f"HoneEp{nm}Zero", h1[setting]["episode_freq_rho0"], f"H1 {setting} episodes rho=0", 2)
        ci(f"HoneEp{nm}Max", h1[setting]["episode_freq_rho_max"], f"H1 {setting} episodes max", 2)
    M("HoneRhoMaxIBM", h1["ibm_small"]["rho_max"], "largest IBM rho", 1)
    h2 = hy["H2"]
    for setting, nm in (("ibm_small", "S"), ("ibm_large", "L")):
        z = h2[setting]["rho0"]
        ci(f"HtwoPC{nm}Zero", z["x2bar"], f"H2 {setting} PC rho=0")
        ci(f"HtwoDC{nm}Zero", z["depth_C"], f"H2 {setting} min coop in episode rho=0")
        ci(f"HtwoRec{nm}Zero", z["recovery_time"], f"H2 {setting} recovery rho=0", 1)
    rows = {q["rho"]: q for q in h2["ibm_small"]["rows"]}
    for rr, nm in ((0.1, "Ten"), (0.3, "Thirty")):
        q = rows[rr]
        ci(f"HtwoPCS{nm}", q["x2bar"], f"H2 small PC rho={rr}")
        ci(f"HtwoDCS{nm}", q["depth_C"], f"H2 small min coop rho={rr}")
        ci(f"HtwoRecS{nm}", q["recovery_time"], f"H2 small recovery rho={rr}", 1)
        ci(f"HtwoDYS{nm}", q["depth_y"], f"H2 small peak corruption rho={rr}")
    ci("HtwoDYSZero", h2["ibm_small"]["rho0"]["depth_y"], "H2 small peak corruption rho=0")
    h3 = hy["H3"]
    M("HthreeNtests", h3["ibm_equivalence_n_tests"], "equivalence tests", kind="raw")
    M("HthreeNexcl", h3["ibm_equivalence_n_excluding_0"], "tests whose CI excludes 0", kind="raw")
    M("HthreeMaxDiff", h3["ibm_equivalence_max_abs_diff"], "max |diff|", 4)
    M("HthreeBonf", "holds" if h3["ibm_equivalence_bonferroni_holds"] else "fails",
      "Bonferroni verdict", kind="raw")
    h4 = hy["H4"]
    a = h4["meanfield_admissible_h"]["ybar"]
    M("HfourInc", a["increasing_pairs"], "pairs where gain increases with h", kind="raw")
    M("HfourPairs", a["pairs"], "pairs", kind="raw")
    c_ = h4["meanfield_admissible_h"]["Cbar"]
    M("HfourIncC", c_["increasing_pairs"], "pairs (cooperation)", kind="raw")
    M("HfourDecC", c_["decreasing_pairs"], "pairs decreasing (cooperation)", kind="raw")
    ib = h4["ibm_small"]
    M("HfourIncIBM", ib["increasing_pairs"], "IBM pairs increasing", kind="raw")
    M("HfourPairsIBM", ib["pairs"], "IBM pairs", kind="raw")
    yz = list(ib["ybar_rho0_by_h"].values())
    M("HfourYZeroMin", min(yz), "IBM honesty rho=0 min over h", 3)
    M("HfourYZeroMax", max(yz), "IBM honesty rho=0 max over h", 3)
    h5 = hy["H5"]
    M("HfiveNscan", h5["default_scan"]["n_scan"], "scan points", kind="raw")
    M("HfiveNbi", h5["default_scan"]["n_bistable"], "bistable points in scan", kind="raw")
    M("HfiveGapPre", h5["preregistered_sweeps_max_gap"], "pre-registered sweep max gap", 3)
    tm = {(m["h"], m["kexp"]): m for m in h5["targeted_maps"]}
    M("HfiveKminDefault", tm[(0.1, 2.0)]["min_kappa_bistable"], "min kappa bistable, default", 2)
    M("HfiveKminStrong", tm[(0.29, 4.0)]["min_kappa_bistable"], "min kappa bistable, h=0.29 k=4",
      2)
    M("HfiveNbiDefault", tm[(0.1, 2.0)]["n_bistable"], "bistable points default map", kind="raw")
    M("HfiveNmap", tm[(0.1, 2.0)]["n"], "map points", kind="raw")
    ph = [s for s in h5["sweeps"] if s["protocol"].startswith("post")]
    gp = [s["max_gap_vs_up"] for s in ph if s["max_gap_vs_up"] is not None]
    M("HfiveGapPost", max(gp), "post-hoc hysteresis gap", 2)
    h6 = hy["H6"]
    M("HsixPoints", h6["points_checked"], "points checked", kind="raw")
    M("HsixMaxRe", h6["max_rightmost_real_part"], "max rightmost real part", 1, "s")
    M("HsixMaxReNeighty", h6["collocation_n80_max_lead"], "max real part, n=80 check", 1, "s")
    for k, nm in (("H1", "One"), ("H2", "Two"), ("H3", "Three"), ("H4", "Four"), ("H5", "Five"),
                  ("H6", "Six")):
        M(f"Outcome{nm}", hy[k]["outcome"], f"{k} outcome", kind="raw")

    # ---- E7 ----
    pl = R("sens_pulse", profile)
    mfp = {(q["rho"], q["tau"]): q for q in pl["meanfield"]}
    M("PulseMFCont", mfp[(0.02, None)]["ybar"], "continuous rho=0.02", 3)
    M("PulseMFFull", mfp[(0.02, 1.0)]["ybar"], "pulse tau=1 rho=0.02", 3)
    ibp = {(c["rho"], c["tau"], c.get("variant", "V0")): c for c in pl["ibm_small"]}
    ci("PulseIBMCont", ibp[(0.03, None, "V0")]["summary"]["ybar"], "IBM continuous rho=0.03")
    ci("PulseIBMFull", ibp[(0.03, 1.0, "V0")]["summary"]["ybar"], "IBM pulse tau=1 rho=0.03")
    p0 = R("sens_p0", profile)
    for k, nm in (("0.9", "Ninety"), ("0.75", "SeventyFive"), ("0.6", "Sixty")):
        M(f"RhoCpZero{nm}", p0["critical"][k]["folds"][0], f"rho_c at p0={k}", 4)
    cur = p0["meanfield"]["0.6"]
    M("PZeroSixtyMin", min(q["ybar"] for q in cur), "min honesty along rho for p0=0.6", 3)
    alt = R("sens_altA", profile)
    M("RhoCAseven", alt["critical"]["folds"][0], "rho_c at A=0.7", 4)
    ex = R("sens_explo", profile)
    M("RhoCMuSmall", ex["0.001"]["critical"]["folds"][0], "rho_c at mu=0.001", 5)
    M("RhoCMuLarge", ex["0.02"]["critical"]["folds"][0], "rho_c at mu=0.02", 4)
    fs = R("sens_finite", profile)
    g = {(c["M"], c["rho"]): c["summary"]["ybar"] for c in fs["ibm"]}
    Ms = sorted(set(c["M"] for c in fs["ibm"]))
    ci("FinSmallZero", g[(Ms[0], 0.0)], "finite M small rho=0")
    ci("FinLargeZero", g[(Ms[-1], 0.0)], "finite M large rho=0")
    ci("FinLargeTen", g[(Ms[-1], 0.1)], "finite M large rho=0.1")
    M("FinMmax", Ms[-1], "largest M", kind="raw")
    nm_ = R("sens_numerics", profile)
    M("TolMaxDiff", max(r["max_abs_diff"] for r in nm_["tolerance"]), "tolerance check max diff",
      1, "s")
    fg = nm_["fine_grid"]
    M("FineGridMaxOff", max(abs(q["first_equilibrium_rho"] - q["rho_c"]) for q in fg
                            if q["first_equilibrium_rho"] is not None), "fine grid offset", 4)
    M("FineGridStep", fg[0]["grid_step"], "fine grid step", 5)
    se = R("sens_se", profile)
    M("SEThirty", se["ybar"]["30"], "SE of ybar at n=30", 4)
    M("SEFifty", se["ybar"]["50"], "SE at n=50", 4)
    M("SEFive", se["ybar"]["5"], "SE at n=5", 4)
    oat = R("sens_oat", profile)
    base = [r for r in oat["meanfield"] if r["param"] == "base"][0]
    probes = [r["ybar_probe"] for r in oat["meanfield"] if r["admissible"]]
    M("OATProbeMin", min(probes), "min honesty at rho=0.05 over admissible OAT", 3)
    M("OATProbeMax", max(probes), "max honesty at rho=0.05 over admissible OAT", 3)
    rcs = [r["crit_folds"][0] for r in oat["meanfield"] if r["admissible"] and r["crit_folds"]]
    M("OATRhoCMin", min(rcs), "min rho_c over admissible OAT", 4)
    M("OATRhoCMax", max(rcs), "max rho_c over admissible OAT", 4)
    M("RhoProbe", oat["rho_probe"], "probe rotation rate", 2)
    sl = {(c["s_factor"], c["rho"]): c["summary"]["ybar"]["mean"] for c in oat["ibm_large_s"]}
    M("SLargeTen", sl[(1.0, 0.1)], "large IBM honesty rho=0.1", 3)
    M("SLargeTenLow", sl[(0.8, 0.1)], "same at 0.8 s", 3)
    M("SLargeTenHigh", sl[(1.2, 0.1)], "same at 1.2 s", 3)
    e4 = R("ext_e4", profile)
    lg = {c["rho"]: c["summary"]["ybar"]["mean"] for c in e4["ibm_large"]}
    nu_l = cfg["ibm_large"]["nu"]
    pred = {r: (nu_l + r) / (2 * nu_l + r) for r in lg}
    M("NeutralMaxDev", max(abs(lg[r] - pred[r]) for r in lg if r >= 0.05),
      "max |ybar - (nu+rho)/(2nu+rho)| for rho>=0.05 (large IBM)", 3)
    # ---- SI verification (branch si-verification) ----
    def opt(name):
        try:
            return R(name, profile)
        except FileNotFoundError:
            return None
    sc = opt("rep_si_compare")
    if sc is not None:
        M("SIVariantsIdentical", "yes" if sc["identical"] else "no",
          "si and reconstructed variants identical", kind="raw")
        ci("SIBthreeRatio", sc["si"]["b3_ratio"], "B3 ratio, si variant")
        ci("RecBthreeRatio", sc["reconstructed"]["b3_ratio"], "B3 ratio, reconstructed variant")
    bd = opt("rep_b3_diag")
    if bd is not None:
        ci("BthreeMajority", bd["baseline"]["ratio_majority"], "B3, majority-time definition")
        ci("BthreePure", bd["baseline"]["ratio_pure"], "B3, all-honest vs all-corrupt time")
        M("BthreePerRepSD", bd["baseline_per_rep_sd"], "SD of per-replicate ratio", 3)
        M("BthreePerRepFrac", bd["baseline_frac_ge_published"], "share of replicates >= 2.15",
          0, "pct")
        for key, nm in (("explore_any", "ExploreAny"), ("role_any", "RoleAny"),
                        ("self_payoff", "SelfPayoff"), ("pair_step", "PairStep")):
            ci(f"Diag{nm}", bd["switches"][key], f"B3 with switch {key}")
        ci("DiagSelThousand", bd["selection"]["1000.0"], "B3 with s = 1e3")
        ci("DiagSelTen", bd["selection"]["10.0"], "B3 with s = 10")
        ci("DiagBurn", bd["burn_in_50000"], "B3 with burn-in 50000 generations")
        ci("DiagStartOC", bd["start_allOC"], "B3 starting from all OC")
        sr = bd["short_runs_1e5_steps"]
        M("ShortRunN", sr["n"], "number of short runs", kind="raw")
        M("ShortRunMean", sr["mean"], "short runs (1e5 steps): mean ratio", 2)
        M("ShortRunSD", sr["sd"], "short runs: SD", 2)
        M("ShortRunQlo", sr["q05"], "short runs: 5% quantile", 2)
        M("ShortRunQhi", sr["q95"], "short runs: 95% quantile", 2)
        M("ShortRunFrac", sr["frac_ge_published"], "short runs: share >= 2.15", 0, "pct")
        lr = bd["long_runs"]
        M("LongRunN", lr["n"], "number of long runs", kind="raw")
        M("LongRunSteps", lr["steps"], "long run length (steps)", 1, "s")
        M("LongRunMean", lr["mean"], "long runs: mean ratio", 3)
        M("LongRunSD", lr["sd"], "long runs: SD", 3)
        M("LongRunMax", max(lr["values"]), "long runs: maximum", 3)
    sic = opt("rep_si_checks")
    if sic is not None:
        for key, v in sic["fig8"].items():
            M(f"SIEight{key}", v["cycles"], f"SI Fig. 8{key} cycles (digitized)", kind="raw")
            M(f"OurEight{key}", v["ours_mean"], f"our cycles at SI Fig. 8{key} settings", 1)
            M(f"OurEight{key}Min", min(v["ours"]), f"min over replicates, 8{key}", kind="raw")
            M(f"OurEight{key}Max", max(v["ours"]), f"max over replicates, 8{key}", kind="raw")
        s10 = [abs(v["rel_diff"]) for v in sic["fig8"].values() if v["s"] >= 10]
        s1 = [v["rel_diff"] for v in sic["fig8"].values() if v["s"] < 10]
        M("EightMaxDevStrong", max(s10), "max |rel diff| of cycle counts, s = 10", 0, "pct")
        M("EightMinDevWeak", min(s1), "min rel diff, s = 1", 0, "pct")
        M("EightMaxDevWeak", max(s1), "max rel diff, s = 1", 0, "pct")
        f9 = [q for q in sic["fig9b"] if q["rel_diff"] is not None]
        good = [abs(q["rel_diff"]) for q in f9 if q["label_period"] != 400]
        M("NineNpoints", len(f9), "SI Fig. 9B label points compared", kind="raw")
        M("NineMaxDev", max(good), "max |rel diff| of period, excluding label 400", 1, "pct")
        M("NineMinDev", min(good), "min |rel diff| of period", 1, "pct")
        q400 = [q for q in f9 if q["label_period"] == 400]
        if q400:
            M("NineDevFourHundred", q400[0]["rel_diff"], "rel diff at label 400", 0, "pct")
        M("HZeroPred", sic["h0"]["markov_prediction"], "h = 0 Markov H:C (SI closed form)", 2)
        mus = sorted(sic["h0"]["ibm"], key=float, reverse=True)
        ci("HZeroIBMA", sic["h0"]["ibm"][mus[0]], f"h = 0 IBM ratio at mu = {mus[0]}", 2)
        ci("HZeroIBMB", sic["h0"]["ibm"][mus[1]], f"h = 0 IBM ratio at mu = {mus[1]}", 2)

    # compute time recorded in the results files
    for prof, nm in ((profile, "Full"), ("quick", "Quick")):
        d = os.path.join(RESULTS, prof)
        tot = 0.0
        for fn in os.listdir(d):
            if fn.endswith(".json") and not fn.startswith("hypotheses"):
                with open(os.path.join(d, fn)) as fh:
                    tot += json.load(fh)["data"].get("runtime_s", 0.0)
        M(f"Runtime{nm}Min", tot / 60.0, f"total recorded compute, {prof} profile (minutes)", 0)
    return MACROS


def main(profile):
    macros = build(profile)
    lines = ["% Auto-generated by experiments/make_numbers.py from results/" + profile + "/.",
             "% Do not edit by hand.", ""]
    for name, val, desc in macros:
        lines.append(f"\\newcommand{{\\{name}}}{{{val}}}  % {desc}")
    path = os.path.join(ROOT, "paper", "autogen_numbers.tex")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    md = ["# Numbers used in the paper (auto-generated)", "", "| macro | value | meaning |",
          "|---|---|---|"]
    md += [f"| \\{n} | {v.replace('|', '/')} | {d} |" for n, v, d in macros]
    with open(os.path.join(RESULTS, profile, "numbers.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(md) + "\n")
    print(f"{len(macros)} macros -> {path}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "full")
