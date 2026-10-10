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


def test_derived_T_matches_printed_except_D4():
    """With the SI fixation rules (SI p.2), our invasion analysis reproduces the printed T except
    the transition allOD(H) -> allOD(C) (D4). The SI text itself says corrupt umpires invade
    (allOD, allH) (SI p.2), but T omits it; state 3 is transient, so the ratio is unchanged.
    (Replaces a pre-SI test that also expected a difference at (4, 2); the SI shows that the
    mu/6 entry is correct: DECISIONS.md D-018.)"""
    Td = rx.derived_T(Params(), MU, LAM, NN)
    Tp = rx.printed_T(MU, LAM, NN)
    D = sp.simplify(Td - Tp)
    nonzero = {(i + 1, j + 1): D[i, j] for i in range(10) for j in range(10) if D[i, j] != 0}
    assert set(nonzero) == {(3, 3), (3, 8)}
    assert sp.simplify(nonzero[(3, 8)] - LAM * MU) == 0


def test_neutral_dissident_rules_from_SI():
    """SI p.2: a PC dissident in allPD (honest) fixes with probability 1/2; a PD dissident in
    allPC (corrupt) cannot fix."""
    ev = rx.derive_transitions(Params())
    pc_in_pd = [e for e in ev if rx.STATE_NAMES[e["frm"]] == "H:allPD" and e["kind"] == "player"
                and e["mutant"] == 1]
    assert len(pc_in_pd) == 1 and pc_in_pd[0]["outcome"] == "neutral_then_advantage"
    assert rx.STATE_NAMES[pc_in_pd[0]["to"]] == "H:allPC"
    pd_in_pc = [e for e in ev if rx.STATE_NAMES[e["frm"]] == "C:allPC" and e["kind"] == "player"
                and e["mutant"] == 3]
    assert pd_in_pc == []


MM = sp.symbols("M", positive=True)


def _si_T_h0(mu, lam, N, M):
    """Transition matrix for cost-free information, h = 0 (SI p.3), rows = from."""
    m, lm = mu, lam * mu
    T = sp.Matrix([
        [0, m / (3 * M), 0, 0, lm / N, 0, 0, 0],
        [m / (3 * M), 0, 0, 0, 0, 0, 0, 0],
        [m / 3, m / 3, 0, m / 3, 0, 0, lm, 0],
        [m / 6, m / 6, 0, 0, 0, 0, 0, lm],
        [lm / N, 0, 0, 0, 0, 0, m / 3, m / 3],
        [0, lm, 0, 0, m / 6, 0, 0, 0],
        [0, 0, 0, 0, 0, m / 3, 0, m / (3 * M)],
        [0, 0, 0, 0, 0, m / 3, m / (3 * M), 0]])
    for i in range(8):
        T[i, i] = 1 - sum(T[i, j] for j in range(8) if j != i)
    return T


def test_cost_free_chain_matches_SI():
    """SI p.3: for h = 0 there are eight absorbing states; our derivation with the SI fixation
    rules (including 1/M for players neutral throughout) reproduces the printed matrix."""
    Td = rx.derived_T(Params(h=0.0), MU, LAM, NN, M=MM)
    assert sp.simplify(Td - _si_T_h0(MU, LAM, NN, MM)) == sp.zeros(8, 8)


def test_cost_free_stationary_distribution_and_ratio():
    """SI p.3: stationary distribution (6L+1+4N, 6L+1+4N+12LM, 0, 0, 6L+1, 4, 6L+1, 6L+1) and
    H:C = 14 + 8N + 12M : 25 at L = 1."""
    pis = rx.stationary_symbolic(rx.derived_T(Params(h=0.0), MU, LAM, NN, M=MM))
    target = [6 * LAM + 1 + 4 * NN, 6 * LAM + 1 + 4 * NN + 12 * LAM * MM, 0, 0, 6 * LAM + 1, 4,
              6 * LAM + 1, 6 * LAM + 1]
    scale = sp.simplify(pis[5] / 4)
    for v, t in zip(pis, target):
        assert sp.simplify(v - scale * t) == 0
    ratio = sp.simplify(sum(pis[:4]) / sum(pis[4:]))
    assert sp.simplify(ratio.subs(LAM, 1) - (14 + 8 * NN + 12 * MM) / 25) == 0


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
    """States 3, 4, 5 receive no transitions from recurrent states, so their rows (D4) do not affect
    the stationary distribution."""
    T = rx.printed_T(1e-3, 1.0, 10)
    pi = rx.stationary(T)
    assert np.allclose(pi[2:5], 0.0, atol=1e-14)
