"""Phase 3 tests: IBM building blocks and agreement with its large-population limit."""
import numpy as np
import pytest

from src.params import Params
from src.ibm import fermi, run_ibm, player_payoff, umpire_payoffs
from src import payoffs as pf
from src.replicator_mutator import Model, integrate, state
from src import analysis as an


def test_fermi_limits_and_ties():
    assert fermi(0.0, 1e10) == 0.5
    assert fermi(0.1, 1e10) == 0.0          # P_X > P_Y: never imitate
    assert fermi(-0.1, 1e10) == 1.0         # P_Y > P_X: always imitate
    assert fermi(1e-3, 0.0) == 0.5          # s = 0: neutral drift
    d = 0.37
    assert fermi(d, 0.3) == pytest.approx(1.0 / (1.0 + np.exp(0.3 * d)))
    assert fermi(d, 2.0) + fermi(-d, 2.0) == pytest.approx(1.0)


def test_ibm_payoffs_match_reference():
    p = Params()
    cnt = np.array([7, 11, 5, 9], dtype=np.int64)
    QH, QC = pf.Q_H(p), pf.Q_C(p)
    ref = pf.player_payoffs_finite(p, cnt, 3, 10)
    got = np.array([player_payoff(i, cnt, float(cnt.sum()), 0.3, QH, QC) for i in range(4)])
    assert np.allclose(got, ref, atol=1e-14)
    assert np.allclose(umpire_payoffs(cnt, float(cnt.sum()), p.f, p.B),
                       pf.umpire_payoffs_finite(p, cnt), atol=1e-14)


def test_counts_conserved_and_bounded():
    r = run_ibm(Params(mu=0.01, nu=0.05), 50, 10, 1e10, 500.0, 0.5, seed=11,
                x0=[0.25, 0.25, 0.25, 0.25], y0=0.5)
    assert np.all(r["counts"].sum(axis=1) == 50)
    assert np.all((r["n_honest"] >= 0) & (r["n_honest"] <= 10))
    assert np.all(r["counts"] >= 0)


def test_neutral_exploration_stationary_means():
    """s = 0: imitation is neutral, exploration symmetric, so means are 1/4 and 1/2."""
    r = run_ibm(Params(mu=0.05, nu=0.05), 400, 200, 0.0, 3000.0, 1.0, seed=12,
                x0=[1, 0, 0, 0], y0=1.0)
    late = r["t"] > 200
    assert np.allclose(r["x"][late].mean(axis=0), 0.25, atol=0.02)
    assert r["y"][late].mean() == pytest.approx(0.5, abs=0.03)


def test_ibm_matches_fermi_mean_field_transient():
    """Large populations follow the exact mean field (DECISIONS D-012) during the transient."""
    p = Params(mu=0.01, nu=0.05)
    s = 0.3
    M, N = 40000, 8000
    T = 60.0
    m = Model(p, kind="fermi", s=s)
    sol = integrate(m, state([0, 0, 1, 0], 1.0), T, t_eval=np.arange(0, T + 1e-9, 1.0))
    errs = []
    for seed in (21, 22):
        r = run_ibm(p, M, N, s, T, 1.0, seed=seed, x0=[0, 0, 1, 0], y0=1.0)
        n = min(len(r["t"]), sol.y.shape[1])
        zi = np.column_stack([r["x"][:n], r["y"][:n]])
        errs.append(np.max(np.abs(zi - sol.y[:, :n].T)))
    assert max(errs) < 0.03


def test_ibm_long_run_mean_matches_mean_field_equilibrium():
    p = Params(mu=0.01, nu=0.05)
    s = 0.3
    m = Model(p, kind="fermi", s=s)
    sol = integrate(m, state([0, 0, 1, 0], 1.0), 20000.0)
    z_eq = sol.y[:, -1]
    assert np.max(np.abs(m.f(0, z_eq))) < 1e-8      # converged to a stable equilibrium
    r = run_ibm(p, 5000, 1000, s, 3000.0, 1.0, seed=23)
    late = r["t"] > 500
    zi = np.concatenate([r["x"][late].mean(axis=0), [r["y"][late].mean()]])
    assert np.max(np.abs(zi - z_eq)) < 0.03


def test_weak_selection_limit_is_replicator_mutator():
    """For small s the Fermi mean field equals the replicator-mutator ODE with time scaled by s/2
    and exploration rates scaled by 2/s (DECISIONS D-012)."""
    s = 1e-4
    mu, nu = 2e-6, 3e-6
    p_f = Params(mu=mu, nu=nu)
    p_r = Params(mu=mu * 2 / s, nu=nu * 2 / s)
    mf = Model(p_f, kind="fermi", s=s)
    mr = Model(p_r, kind="rm")
    rng = np.random.default_rng(7)
    for _ in range(10):
        x = rng.dirichlet(np.ones(4))
        z = state(x, rng.uniform(0.1, 0.9))
        lhs = mf.f(0, z) / (s / 2)
        rhs = mr.f(0, z)
        assert np.allclose(lhs, rhs, atol=1e-4)
