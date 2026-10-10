"""Phase 5 tests: V1 linear inheritance equals fresh rotation at rho_eff = rho (1 - kappa)."""
import numpy as np
import pytest
import sympy as sp

from src.params import Params
from src.replicator_mutator import ROT_V0, ROT_V1, state
from src.rotation import make_model, simulate_meanfield, simulate_pulse_meanfield
from src import analysis as an

P = Params(mu=0.01, nu=0.01)


def test_symbolic_identity():
    rho, kappa, p0, y = sp.symbols("rho kappa p0 y")
    v1 = rho * ((1 - kappa) * p0 + kappa * y - y)
    assert sp.expand(v1 - rho * (1 - kappa) * (p0 - y)) == 0


def test_symbolic_systems_identical():
    """The full reduced V1 system equals the V0 system with rho -> rho (1 - kappa)."""
    u, _, params, rhs1 = an.symbolic_system(ROT_V1)
    _, _, _, rhs0 = an.symbolic_system(ROT_V0)
    names = dict(zip([s.name for s in params], params))
    rho, kappa = names["rho"], names["kappa"]
    diff = (rhs1 - rhs0.subs(rho, rho * (1 - kappa))).applyfunc(sp.expand)
    assert diff == sp.zeros(4, 1)


@pytest.mark.parametrize("rho,kappa", [(0.05, 0.3), (0.2, 0.8), (0.01, 0.5)])
def test_trajectories_identical(rho, kappa):
    t1, Z1 = simulate_meanfield(P, "V1", rho, kappa, p0=0.9, t_burn=0, t_win=3000)
    t0, Z0 = simulate_meanfield(P, "V0", rho * (1 - kappa), 0.0, p0=0.9, t_burn=0, t_win=3000)
    assert np.max(np.abs(Z1 - Z0)) < 1e-7


@pytest.mark.parametrize("tau,kappa", [(0.3, 0.5), (0.5, 0.9)])
def test_pulse_map_identity(tau, kappa):
    """Pulse map: (1 - tau) y + tau((1-k) p0 + k y) = (1 - tau(1-k)) y + tau(1-k) p0."""
    t1, Z1 = simulate_pulse_meanfield(P, "V1", tau, 20.0, kappa, p0=1.0, t_burn=0, t_win=2000)
    t0, Z0 = simulate_pulse_meanfield(P, "V0", tau * (1 - kappa), 20.0, 0.0, p0=1.0, t_burn=0,
                                      t_win=2000)
    assert np.max(np.abs(Z1 - Z0)) < 1e-7


def _bifurcations(p, variant, kappa):
    def mk(r):
        return make_model(p, variant, r, kappa)
    u0 = an.find_equilibria(mk(0.0))[0]
    br = an.continue_equilibria(mk, u0, 0.0, 0.0, 1.0, ds=1e-3)
    folds = sorted(an.refine_fold(mk, br["u"][i], br["lam"][i])[0] for i in br["fold_idx"])
    return folds, br


def test_fold_points_scale_with_one_minus_kappa():
    """Every equilibrium bifurcation of V0 at rho_* appears in V1 at rho_* / (1 - kappa).
    (Default setting: two folds, no Hopf point; see PROGRESS.md.)"""
    kappa = 0.4
    f0, _ = _bifurcations(P, "V0", 0.0)
    f1, _ = _bifurcations(P, "V1", kappa)
    assert len(f0) == 2 and len(f1) == 2
    assert np.allclose(np.array(f1), np.array(f0) / (1 - kappa), rtol=1e-6)


def test_hopf_scales_with_one_minus_kappa_where_present():
    """Near the base Hopf point (mu = nu = 0.06) rotation removes cycles through a Hopf point;
    it scales by 1 / (1 - kappa) too."""
    p = P.with_(mu=0.06, nu=0.06)
    kappa = 0.4

    def mk0(r):
        return make_model(p, "V0", r)

    def mk1(r):
        return make_model(p, "V1", r, kappa)
    _, br0 = _bifurcations(p, "V0", 0.0)
    assert len(br0["hopf_idx"]) >= 1
    i = br0["hopf_idx"][0]
    h0 = an.refine_hopf(mk0, br0["u"][i], br0["lam"][i])
    h1 = an.refine_hopf(mk1, br0["u"][i], br0["lam"][i] / (1 - kappa))
    assert h0 is not None and h1 is not None
    assert h1[0] == pytest.approx(h0[0] / (1 - kappa), rel=1e-6)
    assert h1[2] == pytest.approx(h0[2], rel=1e-6)  # same equilibrium, same frequency


def test_rho_c_approximation_matches_continuation():
    """Small-mu approximation of the critical rotation rate (analysis.rho_c_approx)."""
    for mu in (0.001, 0.003):
        p = P.with_(mu=mu, nu=mu)
        folds, _ = _bifurcations(p, "V0", 0.0)
        approx, _ = an.rho_c_approx(p)
        assert approx == pytest.approx(folds[0], rel=0.02)
