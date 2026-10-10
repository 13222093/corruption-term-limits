"""Phase 5 tests: limits of the rotation extension (rho = 0, kappa = 0) and the DDE solver."""
import numpy as np
import pytest
from scipy.integrate import solve_ivp

from src.params import Params
from src.replicator_mutator import Model, integrate, state
from src.rotation import make_model, simulate_meanfield, simulate_pulse_meanfield
from src.dde import integrate_dde
from src.ibm import run_ibm, ROT_OFF, ROT_CONT, ROT_PULSE, V0, V1, V2, V3

P = Params(mu=0.01, nu=0.01)
RNG = np.random.default_rng(8)
STATES = [state(RNG.dirichlet(np.ones(4)), RNG.uniform(0.05, 0.95)) for _ in range(20)]


@pytest.mark.parametrize("variant", ["V0", "V1", "V2", "V3"])
def test_rho_zero_rhs_equals_base(variant):
    base = Model(P)
    m = make_model(P, variant, rho=0.0, kappa=0.7, p0=0.8)
    for z in STATES:
        assert np.array_equal(m.f(0, z, 0.3), base.f(0, z))


@pytest.mark.parametrize("variant", ["V1", "V2"])
def test_kappa_zero_equals_V0(variant):
    m0 = make_model(P, "V0", rho=0.05, p0=0.9)
    m = make_model(P, variant, rho=0.05, kappa=0.0, p0=0.9)
    for z in STATES:
        assert np.allclose(m.f(0, z), m0.f(0, z), atol=1e-15)


def test_V3_kappa_zero_equals_V0_trajectory():
    t0, Z0 = simulate_meanfield(P, "V0", 0.05, p0=1.0, t_burn=0, t_win=500)
    m = make_model(P, "V3", rho=0.05, kappa=0.0, p0=1.0)
    t3, Z3 = integrate_dde(m, np.array([0.1, 0.4, 0.4, 0.1, 1.0]), 20.0, 500.0, t_eval=t0)
    assert np.max(np.abs(Z3 - Z0)) < 1e-6


def test_meanfield_rho_zero_reproduces_base_trajectory():
    t, Z = simulate_meanfield(P, "V0", 0.0, t_burn=0, t_win=2000)
    # same solver settings as simulate_meanfield, so the trajectories must be identical
    sol = integrate(Model(P), state([0.1, 0.4, 0.4, 0.1], 1.0), 2000, t_eval=t, rtol=1e-9,
                    atol=1e-11)
    assert np.max(np.abs(Z - sol.y.T)) < 1e-12


def test_ibm_rho_zero_identical_to_base():
    kw = dict(p=Params(mu=0.001, nu=0.005), M=50, N=10, s=1e10, t_end=300.0, rec_dt=0.5, seed=5)
    r0 = run_ibm(**kw, rot_mode=ROT_OFF)
    for v in (V0, V1, V2, V3):
        r = run_ibm(**kw, rot_mode=ROT_CONT, rho=0.0, variant=v, kappa=0.5, T_lag=10.0)
        assert np.array_equal(r["counts"], r0["counts"])
        assert np.array_equal(r["n_honest"], r0["n_honest"])


def test_ibm_V1_kappa_zero_identical_to_V0():
    kw = dict(p=Params(mu=0.001, nu=0.005), M=50, N=10, s=1e10, t_end=300.0, rec_dt=0.5, seed=6,
              rot_mode=ROT_CONT, rho=0.1, p0=0.9)
    r0 = run_ibm(**kw, variant=V0)
    r1 = run_ibm(**kw, variant=V1, kappa=0.0)
    assert np.array_equal(r0["n_honest"], r1["n_honest"])


def test_dde_exact_solution():
    """y' = -y(t - 1), y = 1 on [-1, 0]: y = 1 - t on [0, 1], 1 - t + (t - 1)^2 / 2 on [1, 2],
    and 1 - t + (t-1)^2/2 - (t-2)^3/6 on [2, 3]."""
    class Scalar:
        def f(self, t, z, ylag):
            out = np.zeros(5)
            out[4] = -ylag
            return out

    t_eval = np.linspace(0, 3, 61)
    t, Z = integrate_dde(Scalar(), np.array([0, 0, 0, 0, 1.0]), 1.0, 3.0, t_eval=t_eval,
                         rtol=1e-12, atol=1e-14)
    exact = np.where(t <= 1, 1 - t, np.where(t <= 2, 1 - t + (t - 1) ** 2 / 2,
                                             1 - t + (t - 1) ** 2 / 2 - (t - 2) ** 3 / 6))
    assert np.max(np.abs(Z[:, 4] - exact)) < 1e-9


def test_V3_small_lag_approaches_V1():
    m1 = make_model(P, "V1", rho=0.1, kappa=0.6)
    sol = integrate(m1, state([0.1, 0.4, 0.4, 0.1], 1.0), 300, t_eval=np.linspace(0, 300, 601))
    m3 = make_model(P, "V3", rho=0.1, kappa=0.6)
    _, Z = integrate_dde(m3, np.array([0.1, 0.4, 0.4, 0.1, 1.0]), 0.01, 300.0,
                         t_eval=sol.t)
    assert np.max(np.abs(Z - sol.y.T)) < 5e-3


def test_ibm_rotation_relaxation_matches_mean_field():
    """Neutral learning (s = 0, nu = 0): E[y(t)] = p0 + (y0 - p0) exp(-rho t)."""
    rho, p0 = 0.2, 0.6
    ys = []
    for seed in range(6):
        r = run_ibm(Params(mu=0.0, nu=0.0), 100, 2000, 0.0, 20.0, 1.0, seed=100 + seed,
                    x0=[0.25, 0.25, 0.25, 0.25], y0=0.0, rot_mode=ROT_CONT, rho=rho,
                    variant=V0, p0=p0)
        ys.append(r["y"])
    ybar = np.mean(ys, axis=0)
    t = r["t"]
    expected = p0 * (1 - np.exp(-rho * t))
    assert np.max(np.abs(ybar - expected)) < 0.02


def test_ibm_pulse_mean_jump():
    """Neutral learning: after k pulses E[y] = p0 + (1 - tau)^k (y0 - p0)."""
    tau, T, p0 = 0.5, 10.0, 1.0
    ys = []
    for seed in range(6):
        r = run_ibm(Params(mu=0.0, nu=0.0), 100, 2000, 0.0, 45.0, 1.0, seed=200 + seed,
                    x0=[0.25, 0.25, 0.25, 0.25], y0=0.0, rot_mode=ROT_PULSE, pulse_T=T,
                    pulse_tau=tau, variant=V0, p0=p0)
        ys.append(r["y"])
    ybar = np.mean(ys, axis=0)
    t = r["t"]
    k = np.floor(t / T + 1e-9)
    expected = p0 + (1 - tau) ** k * (0.0 - p0)
    assert np.max(np.abs(ybar - expected)) < 0.02


def test_ibm_V3_matches_delay_equation():
    """Neutral learning with delayed inheritance follows y' = rho((1-k) p0 + k y(t-L) - y)."""
    rho, kappa, p0, L = 0.3, 0.8, 1.0, 4.0
    ys = []
    for seed in range(6):
        r = run_ibm(Params(mu=0.0, nu=0.0), 100, 3000, 0.0, 30.0, 0.5, seed=300 + seed,
                    x0=[0.25, 0.25, 0.25, 0.25], y0=0.0, rot_mode=ROT_CONT, rho=rho,
                    variant=V3, p0=p0, kappa=kappa, T_lag=L, hist_dt=0.05)
        ys.append(r["y"])
    ybar = np.mean(ys, axis=0)

    class Pure:
        def f(self, t, z, ylag):
            out = np.zeros(5)
            out[4] = rho * ((1 - kappa) * p0 + kappa * ylag - z[4])
            return out

    t, Z = integrate_dde(Pure(), np.zeros(5), L, 30.0, t_eval=r["t"])
    assert np.max(np.abs(ybar - Z[:, 4])) < 0.02


def test_pulse_meanfield_no_pulse_effect_when_tau_zero():
    t, Z = simulate_pulse_meanfield(P, "V0", 0.0, 10.0, t_burn=0, t_win=300)
    sol = integrate(Model(P), state([0.1, 0.4, 0.4, 0.1], 1.0), 300, t_eval=t)
    assert np.max(np.abs(Z - sol.y.T)) < 1e-6
