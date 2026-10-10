"""Phase 4 tests: rare-exploration Markov chain (Methods p.13281)."""
import numpy as np
import pytest
import sympy as sp

from src.params import Params
from src import rare_exploration as rx

MU, LAM, NN = sp.symbols("mu lambda N", positive=True)


def test_printed_T_rows_sum_to_one():
    T = rx.printed_T(0.01, 1.3, 10)
    assert np.allclose(T.sum(axis=1), 1.0)
    assert np.all(T >= 0)


def test_paper_stationary_vector_is_stationary_for_printed_T():
    for lam in (0.5, 1.0, 2.0):
        for N in (5, 10, 40):
            T = rx.printed_T(1e-3, lam, N)
            pi = np.array(rx.paper_stationary(lam, N), dtype=float)
            pi = pi / pi.sum()
            assert np.allclose(pi @ T, pi, atol=1e-15)
            assert np.allclose(rx.stationary(T), pi, atol=1e-12)


def test_hc_ratio_formula_symbolic():
    pis = rx.stationary_symbolic(rx.printed_T(MU, LAM, NN))
    ratio = sp.simplify(sum(pis[:5]) / sum(pis[5:]))
    paper = ((7 + 12 * LAM) * NN + 33 * LAM + 54 * LAM ** 2) / (7 + 48 * LAM + 54 * LAM ** 2)
    assert sp.simplify(ratio - paper) == 0
    assert float(paper.subs({LAM: 1, NN: 10})) == pytest.approx(277 / 109)


def test_lambda_one_frequencies():
    """Methods p.13281: at lambda = 1 the frequencies are (1/15)(19N+30, 57, 0,0,0, 30, 3, 45, 15, 16)."""
    N = 10
    pi = np.array(rx.paper_stationary(1.0, N))
    expected = np.array([19 * N + 30, 57, 0, 0, 0, 30, 3, 45, 15, 16]) / 15
    assert np.allclose(pi, expected)


def test_derived_T_matches_printed_except_documented_entries():
    """Our invasion analysis reproduces T except rows 3 and 4 (SPEC D4, D5)."""
    Td = rx.derived_T(Params(), MU, LAM, NN)
    Tp = rx.printed_T(MU, LAM, NN)
    D = sp.simplify(Td - Tp)
    nonzero = {(i + 1, j + 1): D[i, j] for i in range(10) for j in range(10) if D[i, j] != 0}
    assert set(nonzero) == {(3, 3), (3, 8), (4, 2), (4, 4)}
    assert sp.simplify(nonzero[(3, 8)] - LAM * MU) == 0
    assert sp.simplify(nonzero[(4, 2)] + MU / 6) == 0


def test_derived_T_same_ratio():
    pis = rx.stationary_symbolic(rx.derived_T(Params(), MU, LAM, NN))
    ratio = sp.simplify(sum(pis[:5]) / sum(pis[5:]))
    paper = ((7 + 12 * LAM) * NN + 33 * LAM + 54 * LAM ** 2) / (7 + 48 * LAM + 54 * LAM ** 2)
    assert sp.simplify(ratio - paper) == 0


@pytest.mark.parametrize("p", [Params(), Params(A=0.7), Params(b=1.4, c=0.6, f=0.15, B=0.25,
                                                                  h=0.08, A=1.5)])
def test_ratio_independent_of_game_parameters(p):
    """p.13279: the ratio does not depend on M, A, B, f, h, b, c (given Eqs. 1-4)."""
    T = rx.derived_T(p, 1e-3, 1.0, 10)
    assert rx.hc_ratio(rx.stationary(T)) == pytest.approx(277 / 109, rel=1e-10)


def test_states_3_4_5_transient():
    """States 3, 4, 5 receive no transitions from recurrent states, so D4, D5 are harmless."""
    T = rx.printed_T(1e-3, 1.0, 10)
    pi = rx.stationary(T)
    assert np.allclose(pi[2:5], 0.0, atol=1e-14)
