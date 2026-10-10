"""Tests that encode rules stated in the SI Appendix of Lee et al. (2019)
(refs/pnas.1900078116.sapp.pdf). Page numbers refer to the SI ("x of 10")."""
import numpy as np
import pytest

from src.params import Params, OC, PC, OD, PD
from src.ibm import fermi, player_payoff, run_ibm
from src.ibm_diag import run_diag
from src.payoffs import Q_C, Q_H
from src.utils import load_config

BASE = Params()


def test_variants_si_and_reconstructed_identical():
    """The SI states no rule that differs from the reconstruction, so both variants run the same
    process (DECISIONS.md D-017)."""
    kw = dict(p=Params(mu=0.001, nu=0.005), M=50, N=10, s=1e10, t_end=500.0, rec_dt=0.5, seed=3)
    a = run_ibm(**kw, ibm_variant="si")
    b = run_ibm(**kw, ibm_variant="reconstructed")
    assert np.array_equal(a["counts"], b["counts"])
    assert np.array_equal(a["n_honest"], b["n_honest"])


def test_unknown_variant_rejected():
    with pytest.raises(ValueError):
        run_ibm(Params(), 10, 5, 1.0, 1.0, 1.0, 1, ibm_variant="authors")


@pytest.mark.parametrize("setting", ["ibm_small", "ibm_large"])
def test_umpire_exploration_rate_is_mu_M_over_N(setting):
    """SI Fig. 7 caption: the umpire exploration rate is nu = mu M / N (= 5 mu for Fig. 1)."""
    S = load_config("full")[setting]
    assert S["nu"] == pytest.approx(S["mu"] * S["M"] / S["N"])


def test_player_exploration_goes_to_the_other_three_strategies():
    """SI p.2: an exploration step leads a player from the resident strategy to one of the three
    alternative strategies with equal probability (never to its own)."""
    M, N = 30000, 10
    p = Params(mu=1.0, nu=0.0)
    r = run_ibm(p, M, N, 0.0, 0.05, 0.05, seed=5, x0=[1, 0, 0, 0], y0=1.0)
    cnt = r["counts"][-1]
    switched = M - cnt[OC]
    # every player update switched strategy: compare with the expected number of player updates
    expected_updates = 0.05 * (M + N) * M / (M + N)
    assert switched == pytest.approx(expected_updates, rel=0.05)
    shares = cnt[1:] / cnt[1:].sum()
    assert np.allclose(shares, 1 / 3, atol=0.03)


def test_umpire_exploration_flips_type_without_role_model():
    """SI p.2: an exploring umpire switches to the alternative strategy at random. With nu = 1
    every umpire update flips the type, so E[y](t) = 1/2 + exp(-2t)/2."""
    ys = []
    for seed in range(8):
        r = run_ibm(Params(mu=0.0, nu=1.0), 20, 2000, 0.0, 0.6, 0.3, seed=seed, x0=[1, 0, 0, 0],
                    y0=1.0)
        ys.append(r["y"])
    yb = np.mean(ys, axis=0)
    t = r["t"]
    assert np.allclose(yb, 0.5 + 0.5 * np.exp(-2 * t), atol=0.02)


def test_ties_imitated_with_probability_half():
    """Main text Methods and SI p.2: equal payoffs lead to imitation with probability 1/2."""
    assert fermi(0.0, 1e10) == 0.5
    assert fermi(0.0, 10.0) == 0.5


def test_single_neutral_dissident_payoffs():
    """SI p.2: a PC dissident among PD residents (honest umpires) does exactly as well as the
    residents; with two PC players, PC does better. A PD dissident among PC residents (corrupt
    umpires) does as well; with two PD players, PD does worse. This holds only if a player's
    co-player is drawn from the other M - 1 players."""
    M = 40
    QH, QC = Q_H(BASE), Q_C(BASE)
    c1 = np.array([0, 1, 0, M - 1], dtype=np.int64)
    c2 = np.array([0, 2, 0, M - 2], dtype=np.int64)
    assert player_payoff(PC, c1, float(M), 1.0, QH, QC) == pytest.approx(
        player_payoff(PD, c1, float(M), 1.0, QH, QC), abs=1e-15)
    assert player_payoff(PC, c2, float(M), 1.0, QH, QC) > player_payoff(PD, c2, float(M), 1.0, QH, QC)
    d1 = np.array([0, M - 1, 0, 1], dtype=np.int64)
    d2 = np.array([0, M - 2, 0, 2], dtype=np.int64)
    assert player_payoff(PD, d1, float(M), 0.0, QH, QC) == pytest.approx(
        player_payoff(PC, d1, float(M), 0.0, QH, QC), abs=1e-15)
    assert player_payoff(PD, d2, float(M), 0.0, QH, QC) < player_payoff(PC, d2, float(M), 0.0, QH, QC)


def _absorb(M, N, x0, y0, runs, t_end=400.0):
    out = []
    for k in range(runs):
        r = run_ibm(Params(mu=0.0, nu=0.0), M, N, 1e10, t_end, t_end, seed=10_000 + k,
                    x0=x0, y0=y0)
        out.append((r["counts"][-1], r["n_honest"][-1]))
    return out


def test_pc_dissident_in_allPD_fixes_with_probability_half():
    """SI p.2: with hard imitation, a PC dissident in an allPD population (honest umpires) reaches
    fixation with probability 1/2 (entry mu/6 of T)."""
    M, N, runs = 20, 4, 600
    res = _absorb(M, N, [0, 1 / M, 0, 1 - 1 / M], 1.0, runs)
    fixed = np.mean([c[PC] == M for c, _ in res])
    lost = np.mean([c[PD] == M for c, _ in res])
    assert fixed + lost == pytest.approx(1.0)
    assert fixed == pytest.approx(0.5, abs=0.06)


def test_pd_dissident_in_allPC_never_fixes():
    """SI p.2: a PD dissident among PC residents (corrupt umpires) cannot yield to PD; the
    population returns to allPC."""
    M, N = 20, 4
    res = _absorb(M, N, [0, 1 - 1 / M, 0, 1 / M], 0.0, 200)
    assert all(c[PC] == M for c, _ in res)


def test_neutral_umpire_fixes_with_probability_one_over_N():
    """SI p.2: in an OC population a dissident corrupt umpire replaces the honest residents with
    the neutral fixation probability 1/N."""
    M, N, runs = 10, 5, 1500
    res = _absorb(M, N, [1, 0, 0, 0], 1 - 1 / N, runs, t_end=600.0)
    corrupt_fixed = np.mean([h == 0 for _, h in res])
    assert all(h in (0, N) for _, h in res)
    assert corrupt_fixed == pytest.approx(1 / N, abs=0.035)


def test_time_unit_one_generation_is_M_plus_N_updates():
    """Time unit (SPEC A1): one generation is M + N elementary update events, so the per-step
    speed scales with 1/(M + N) (supported by SI Fig. 8: smaller populations cycle faster)."""
    M, N, T = 50, 10, 200.0
    r = run_ibm(Params(mu=0.001, nu=0.005), M, N, 1e10, T, 1.0, seed=2)
    assert abs(r["n_events"] - T * (M + N)) <= 2


def test_diag_kernel_matches_main_kernel_when_switches_off():
    kw = dict(p=Params(mu=0.001, nu=0.005), M=50, N=10, s=1e10, t_end=400.0, rec_dt=0.5,
              seed=21)
    a = run_ibm(**kw)
    b = run_diag(**kw)
    assert np.array_equal(a["counts"], b["counts"])
    assert np.array_equal(a["n_honest"], b["n_honest"])


@pytest.mark.parametrize("switch", ["explore_any", "role_any", "self_payoff", "pair_step"])
def test_diag_switches_change_the_process(switch):
    kw = dict(p=Params(mu=0.01, nu=0.05), M=50, N=10, s=1e10, t_end=400.0, rec_dt=0.5, seed=22)
    a = run_diag(**kw)
    b = run_diag(**kw, **{switch: True})
    assert not np.array_equal(a["n_honest"], b["n_honest"])
