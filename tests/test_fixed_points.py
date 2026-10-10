"""Phase 2 tests: replicator-mutator ODE, fixed points, Jacobian, DDE roots, B1 and B2."""
import numpy as np
import pytest

from src.params import Params, OC, PC, OD, PD
from src.replicator_mutator import Model, integrate, state, ROT_NONE, ROT_V0, ROT_V1, ROT_V2
from src import analysis as an

BASE = Params()
OTHER = Params(b=1.4, c=0.6, f=0.15, B=0.25, h=0.08, A=1.5)  # also satisfies Eqs. 1-4


def _limit(model, x0, y0, T=40000.0):
    sol = integrate(model, state(x0, y0), T)
    return sol.y[:, -1]


@pytest.mark.parametrize("p", [BASE, OTHER])
def test_B1_all_corrupt(p):
    """Text p.13278: all umpires corrupt -> OD = h/(f+B), PC = (f+B-h)/(f+B)."""
    m = Model(p.with_(mu=0.0, nu=0.0))
    rng = np.random.default_rng(3)
    target = np.array([0.0, (p.f + p.B - p.h) / (p.f + p.B), p.h / (p.f + p.B), 0.0])
    for _ in range(4):
        z = _limit(m, rng.dirichlet(np.ones(4)), 0.0)
        assert z[4] == 0.0
        assert np.allclose(z[:4], target, atol=1e-5)


@pytest.mark.parametrize("p", [BASE, OTHER])
def test_B2_all_honest(p):
    """Text p.13278: all umpires honest -> OC converges to 1."""
    m = Model(p.with_(mu=0.0, nu=0.0))
    rng = np.random.default_rng(4)
    for _ in range(4):
        z = _limit(m, rng.dirichlet(np.ones(4)), 1.0)
        assert z[OC] > 1 - 1e-5


def test_printed_weighting_fails_B1():
    """With Q(y) = y Q_C + (1-y) Q_H as printed, y = 0 gives Q_H and OC -> 1, contradicting B1."""
    p = BASE.with_(mu=0.0, nu=0.0)
    m = Model(p)
    m.QH, m.QC = m.QC.copy(), m.QH.copy()  # printed weighting
    z = _limit(m, np.array([0.25, 0.25, 0.25, 0.25]), 0.0)
    assert z[OC] > 0.99
    assert abs(z[OD] - p.h / (p.f + p.B)) > 0.2


def test_fig2_fixed_points_are_equilibria():
    p = BASE.with_(mu=0.0, nu=0.0)
    m = Model(p)
    fp5 = state([0, 0, p.h / (p.f + p.A), (p.f + p.A - p.h) / (p.f + p.A)], 1.0)
    fp10 = state([0, (p.f + p.B - p.h) / (p.f + p.B), p.h / (p.f + p.B), 0], 0.0)
    assert np.max(np.abs(m.f(0, fp5))) < 1e-14
    assert np.max(np.abs(m.f(0, fp10))) < 1e-14
    for y in np.linspace(0, 1, 11):  # edge of fixed points x = (1,0,0,0)
        assert np.max(np.abs(m.f(0, state([1, 0, 0, 0], y)))) < 1e-14
    for v in range(4):  # the eight homogeneous states
        for y in (0.0, 1.0):
            x = np.zeros(4)
            x[v] = 1.0
            assert np.max(np.abs(m.f(0, state(x, y)))) < 1e-14


def test_condition4_honest_invades_fp10():
    """p.13278: h < sqrt(f(f+B)) guarantees that honest umpires can invade fixed point 10."""
    for h, invades in [(0.1, True), (0.27, True), (0.29, False)]:
        p = BASE.with_(h=h)
        x = np.array([0, (p.f + p.B - p.h) / (p.f + p.B), p.h / (p.f + p.B), 0])
        dP = 2 * p.f * (x[1] - x[3]) * (1 + x[0] + x[2]) - 2 * p.B * (x[2] + x[3]) * (1 - x[1])
        assert (dP > 0) == invades


@pytest.mark.parametrize("variant,rho", [(ROT_NONE, 0.0), (ROT_V0, 0.1), (ROT_V1, 0.1),
                                         (ROT_V2, 0.1)])
def test_symbolic_matches_numba(variant, rho):
    m = Model(BASE.with_(mu=0.01, nu=0.02), rho=rho, variant=variant, p0=0.9, kappa=0.4)
    rng = np.random.default_rng(5)
    for _ in range(20):
        x = rng.dirichlet(np.ones(4))
        u = np.array([x[0], x[1], x[2], rng.uniform(0.05, 0.95)])
        assert np.allclose(an.symbolic_rhs(m, u), an.reduced_rhs(m, u), atol=1e-13)
        assert np.allclose(an.jacobian(m, u), an.numeric_jacobian(m, u), atol=1e-7)


def test_simplex_is_conserved():
    m = Model(BASE.with_(mu=1e-3, nu=1e-3))
    sol = integrate(m, state([0.1, 0.4, 0.4, 0.1], 1.0), 20000, t_eval=np.linspace(0, 20000, 2001))
    S = sol.y[:4].sum(axis=0)
    assert np.max(np.abs(S - 1)) < 1e-8
    assert np.all(sol.y[:4] > -1e-10)


def test_dde_roots_scalar_known_boundary():
    """x' = -x(t - tau) is stable iff tau < pi/2; at tau = pi/2 the roots are +-i."""
    J0 = np.zeros((1, 1))
    J1 = -np.ones((1, 1))
    assert an.dde_char_roots(J0, J1, 1.5)[0].real < 0
    assert an.dde_char_roots(J0, J1, 1.65)[0].real > 0
    r = an.dde_char_roots(J0, J1, np.pi / 2, n=60)[0]
    assert abs(r.real) < 1e-8 and abs(abs(r.imag) - 1.0) < 1e-8


def test_dde_roots_reduce_to_ode_without_delay():
    rng = np.random.default_rng(6)
    J0 = rng.normal(size=(3, 3))
    J1 = rng.normal(size=(3, 3)) * 0.3
    r_small = an.dde_char_roots(J0, J1, 1e-6, n=30)[0]
    r_ode = np.linalg.eigvals(J0 + J1)
    assert np.min(np.abs(r_ode - r_small)) < 1e-4


def test_interior_equilibrium_and_hopf_in_exploration():
    """Orbit shrinkage (Fig. 3): a stable equilibrium at mu = nu = 0.07, unstable at 0.02."""
    def mk(v):
        return Model(BASE.with_(mu=v, nu=v))
    eq = an.find_equilibria(mk(0.07))
    interior = [u for u in eq if np.all(an.full_state(u)[:4] > 1e-3) and 0.01 < u[3] < 0.99]
    assert len(interior) == 1
    ev = an.eigenvalues(mk(0.07), interior[0])
    assert ev[0].real < 0
    hopf = an.locate_hopf(mk, 0.02, 0.07, interior[0])
    assert hopf is not None
    assert 0.02 < hopf[0] < 0.07
