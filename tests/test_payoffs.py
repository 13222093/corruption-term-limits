"""Tests for payoff matrices and umpire income (Phase 1).

Checks: (1) matrices equal the outcome of the rule-based game (p.13277) for every strategy pair;
(2) explicit signs of selected entries at symbolic level; (3) umpire income by brute-force
enumeration of player pairs equals the printed P_H - P_C (Methods p.13281); (4) inequalities.
"""
import itertools
import math

import numpy as np
import pytest
import sympy as sp

from src.params import OC, PC, OD, PD, H, C, Params, check_inequalities, inequalities
from src import payoffs as pf


BASE = Params()
RANDOM_PARAMS = [
    Params(b=1.3, c=0.4, f=0.15, B=0.1, h=0.05, A=1.1),
    Params(b=2.0, c=0.9, f=0.3, B=0.25, h=0.2, A=3.0),
    BASE,
]


@pytest.mark.parametrize("p", RANDOM_PARAMS)
@pytest.mark.parametrize("umpire", [H, C])
def test_matrices_match_rule_based_game(p, umpire):
    Q = pf.Q_H(p) if umpire == H else pf.Q_C(p)
    for s1, s2 in itertools.product(range(4), repeat=2):
        g1, g2, _ = pf.play_game(p, s1, s2, umpire)
        assert Q[s1, s2] == pytest.approx(g1, abs=1e-14)
        assert Q[s2, s1] == pytest.approx(g2, abs=1e-14)


def test_symbolic_signs_from_pdf():
    """Signs read from the PDF at 300 dpi (Methods p.13280), checked symbolically."""
    b, c, f, h, A, B = sp.symbols("b c f h A B", positive=True)
    p = Params(b=b, c=c, f=f, B=B, h=h, A=A)
    # Symbolic matrices from the rule-based game, compared with the matrices printed in the PDF.
    QHs = sp.Matrix(4, 4, lambda i, j: pf.play_game(p, i, j, H)[0])
    QCs = sp.Matrix(4, 4, lambda i, j: pf.play_game(p, i, j, C)[0])
    expected_H = sp.Matrix([
        [b - c - f, b - c - f, -c - f, 0],
        [b - c - f - h, b - c - f - h, -c - f - h, -h],
        [b - f - A, b - f - A, -f - A, 0],
        [-h, -h, -h, -h],
    ])
    expected_C = sp.Matrix([
        [b - c - f, 0, -c - f, -c - f],
        [-h, -h, -h, -h],
        [b - f - B, 0, -f - B, -f - B],
        [b - f - B - h, -h, -f - B - h, -f - B - h],
    ])
    assert sp.simplify(QHs - expected_H) == sp.zeros(4, 4)
    assert sp.simplify(QCs - expected_C) == sp.zeros(4, 4)
    # The numeric implementation agrees with the printed matrices at random parameter values.
    vals = {b: 1.7, c: 0.6, f: 0.25, h: 0.07, A: 1.9, B: 0.15}
    pn = Params(b=1.7, c=0.6, f=0.25, B=0.15, h=0.07, A=1.9)
    assert np.allclose(pf.Q_H(pn), np.array(expected_H.subs(vals), dtype=float))
    assert np.allclose(pf.Q_C(pn), np.array(expected_C.subs(vals), dtype=float))


def _umpire_income_enumeration(p, x):
    """Expected umpire income by enumerating all ordered pairs of strategies."""
    PH = PCr = 0.0
    for s1, s2 in itertools.product(range(4), repeat=2):
        w = x[s1] * x[s2]
        PH += w * pf.play_game(p, s1, s2, H)[2]
        PCr += w * pf.play_game(p, s1, s2, C)[2]
    return PH, PCr


@pytest.mark.parametrize("p", RANDOM_PARAMS)
def test_umpire_income_enumeration_matches_paper_formula(p):
    rng = np.random.default_rng(1)
    for _ in range(200):
        x = rng.dirichlet(np.ones(4))
        PH, PCr = _umpire_income_enumeration(p, x)
        PH2, PC2 = pf.umpire_payoffs(p, x)
        assert PH == pytest.approx(PH2, abs=1e-13)
        assert PCr == pytest.approx(PC2, abs=1e-13)
        assert PH - PCr == pytest.approx(pf.umpire_diff_paper(p, x), abs=1e-13)


def test_umpire_difference_symbolic():
    x1, x2, x3, f, B = sp.symbols("x1 x2 x3 f B")
    x4 = 1 - x1 - x2 - x3
    PH = 2 * f * (1 - x4) ** 2
    PCr = 2 * f * (1 - x2) ** 2 + 2 * B * (x3 + x4) * (1 - x2)
    printed = 2 * f * (x2 - x4) * (1 + x1 + x3) - 2 * B * (x3 + x4) * (1 - x2)
    assert sp.expand(PH - PCr - printed) == 0


def test_umpire_income_cases_from_text():
    """Spot checks of the income rules quoted in Methods p.13280."""
    p = BASE
    assert pf.play_game(p, OC, PD, H)[2] == 0.0          # PD present: honest gets 0
    assert pf.play_game(p, OC, OC, H)[2] == pytest.approx(2 * p.f)
    assert pf.play_game(p, OC, PC, C)[2] == 0.0          # PC present: corrupt gets 0
    assert pf.play_game(p, OC, OD, C)[2] == pytest.approx(2 * p.f + p.B)
    assert pf.play_game(p, PD, OD, C)[2] == pytest.approx(2 * p.f + 2 * p.B)


def test_base_inequalities_hold():
    assert check_inequalities(BASE)
    ineq = inequalities(BASE)
    assert ineq["eq4_h<sqrt(f(f+B))"][1] == pytest.approx(math.sqrt(0.08))


@pytest.mark.parametrize("kw,key", [
    (dict(h=0.31), "eq1_f+h<b-c"),
    (dict(A=0.55), "eq2_c+h<A"),
    (dict(B=0.45), "eq3_B+h<c"),
    (dict(h=0.29), "eq4_h<sqrt(f(f+B))"),
])
def test_inequality_violations_detected(kw, key):
    p = BASE.with_(**kw)
    assert not inequalities(p)[key][2]
    assert not check_inequalities(p)


def test_finite_population_payoffs_converge():
    rng = np.random.default_rng(2)
    x = rng.dirichlet(np.ones(4))
    y = 0.37
    for M in (10**4, 10**6):
        counts = np.round(x * M)
        xm = counts / counts.sum()
        N = 1000
        n_h = int(round(y * N))
        Pf = pf.player_payoffs_finite(BASE, counts, n_h, N)
        Pi = pf.player_payoffs(BASE, xm, n_h / N)
        assert np.max(np.abs(Pf - Pi)) < 10.0 / M
        PH, PCr = pf.umpire_payoffs_finite(BASE, counts)
        PH2, PC2 = pf.umpire_payoffs(BASE, xm)
        assert abs(PH - PH2) < 10.0 / M and abs(PCr - PC2) < 10.0 / M


def test_finite_umpire_payoffs_by_pair_enumeration():
    """Exact check for a tiny population: average over all ordered pairs of distinct players."""
    p = BASE
    counts = np.array([2, 1, 3, 2])
    pop = np.repeat(np.arange(4), counts)
    PH = PCr = 0.0
    n = 0
    for i, j in itertools.permutations(range(len(pop)), 2):
        PH += pf.play_game(p, pop[i], pop[j], H)[2]
        PCr += pf.play_game(p, pop[i], pop[j], C)[2]
        n += 1
    PH2, PC2 = pf.umpire_payoffs_finite(p, counts)
    assert PH / n == pytest.approx(PH2, abs=1e-14)
    assert PCr / n == pytest.approx(PC2, abs=1e-14)


def test_finite_player_payoffs_by_enumeration():
    p = BASE
    counts = np.array([2, 1, 3, 2])
    pop = np.repeat(np.arange(4), counts)
    n_h, N = 3, 7
    y = n_h / N
    expected = np.zeros(4)
    for s in range(4):
        focal = int(np.where(pop == s)[0][0])
        tot = 0.0
        for j in range(len(pop)):
            if j == focal:
                continue
            tot += y * pf.play_game(p, s, pop[j], H)[0] + (1 - y) * pf.play_game(p, s, pop[j], C)[0]
        expected[s] = tot / (len(pop) - 1)
    got = pf.player_payoffs_finite(p, counts, n_h, N)
    assert np.allclose(got, expected, atol=1e-14)


def test_tie_at_all_oc_is_exact():
    """At allOC, honest and corrupt umpires earn exactly 2f (neutral drift; DECISIONS D-007)."""
    for M in (50, 5000):
        counts = np.array([M, 0, 0, 0])
        PH, PCr = pf.umpire_payoffs_finite(BASE, counts)
        assert PH == PCr
