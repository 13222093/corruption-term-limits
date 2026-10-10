"""Mean-field analysis: equilibria, Jacobians, stability, Hopf points, DDE characteristic roots.

Reduced coordinates u = (x1, x2, x3, y) with x4 = 1 - x1 - x2 - x3 (the simplex is invariant).
The symbolic Jacobian is built with sympy from the published equations (Methods p.13281, with
the Q(y) weighting of DECISIONS D-001) plus the rotation term of CLAUDE.md Section 6.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np
import sympy as sp
from scipy.optimize import brentq, root

from .params import Params
from .replicator_mutator import ROT_NONE, ROT_V0, ROT_V1, ROT_V2, Model

SYM_NAMES = ("b", "c", "f", "B", "h", "A", "mu", "nu", "rho", "p0", "kappa", "kexp")


@lru_cache(maxsize=None)
def symbolic_system(variant: int, delayed: bool = False):
    """Return (u_syms, ylag_sym, param_syms, rhs_expr) of the reduced 4D replicator-mutator system.

    variant: ROT_NONE, ROT_V0, ROT_V1 or ROT_V2. If delayed is True the inheritance term uses the
    symbol ylag (V3: p_new = (1 - kappa) p0 + kappa ylag).
    """
    x1, x2, x3, y, ylag = sp.symbols("x1 x2 x3 y ylag")
    b, c, f, B, h, A, mu, nu, rho, p0, kappa, kexp = sp.symbols(" ".join(SYM_NAMES))
    x4 = 1 - x1 - x2 - x3
    x = sp.Matrix([x1, x2, x3, x4])
    QH = sp.Matrix([
        [b - c - f, b - c - f, -c - f, 0],
        [b - c - f - h, b - c - f - h, -c - f - h, -h],
        [b - f - A, b - f - A, -f - A, 0],
        [-h, -h, -h, -h],
    ])
    QC = sp.Matrix([
        [b - c - f, 0, -c - f, -c - f],
        [-h, -h, -h, -h],
        [b - f - B, 0, -f - B, -f - B],
        [b - f - B - h, -h, -f - B - h, -f - B - h],
    ])
    Q = y * QH + (1 - y) * QC
    fit = Q * x
    fbar = (x.T * fit)[0, 0]
    dx = [x[i] * (fit[i] - fbar) - mu * x[i] + mu * (1 - x[i]) / 3 for i in range(3)]
    dP = 2 * f * (x2 - x4) * (1 + x1 + x3) - 2 * B * (x3 + x4) * (1 - x2)
    dy = y * (1 - y) * dP - nu * y + nu * (1 - y)
    if delayed:
        dy += rho * ((1 - kappa) * p0 + kappa * ylag - y)
    elif variant == ROT_V0:
        dy += rho * (p0 - y)
    elif variant == ROT_V1:
        dy += rho * ((1 - kappa) * p0 + kappa * y - y)
    elif variant == ROT_V2:
        g = y ** kexp / (y ** kexp + (1 - y) ** kexp)
        dy += rho * ((1 - kappa) * p0 + kappa * g - y)
    rhs = sp.Matrix(dx + [dy])
    params = sp.symbols(" ".join(SYM_NAMES))
    return (x1, x2, x3, y), ylag, params, rhs


@lru_cache(maxsize=None)
def _lambdified(variant: int, delayed: bool):
    u, ylag, params, rhs = symbolic_system(variant, delayed)
    J = rhs.jacobian(sp.Matrix(u))
    args = list(u) + [ylag] + list(params)
    f_rhs = sp.lambdify(args, rhs, "numpy")
    f_J = sp.lambdify(args, J, "numpy")
    f_Jlag = None
    if delayed:
        f_Jlag = sp.lambdify(args, rhs.jacobian(sp.Matrix([ylag])), "numpy")
    return f_rhs, f_J, f_Jlag


def _param_values(model: Model):
    p = model.p
    return [p.b, p.c, p.f, p.B, p.h, p.A, p.mu, p.nu, model.rho, model.p0, model.kappa,
            model.kexp]


def full_state(u) -> np.ndarray:
    u = np.asarray(u, dtype=float)
    return np.array([u[0], u[1], u[2], 1.0 - u[0] - u[1] - u[2], u[3]])


def reduced_rhs(model: Model, u, ylag=None) -> np.ndarray:
    """Reduced right-hand side using the numba implementation (for root finding)."""
    z = full_state(u)
    yl = z[4] if ylag is None else ylag
    dz = model.f(0.0, z, yl)
    return np.array([dz[0], dz[1], dz[2], dz[4]])


def jacobian(model: Model, u, delayed: bool = False, ylag=None):
    """Symbolic Jacobian of the reduced system. For delayed=True returns (J0, J1)."""
    if model.kind != "rm":
        return numeric_jacobian(model, u)
    variant = model.variant if model.rho > 0 else ROT_NONE
    f_rhs, f_J, f_Jlag = _lambdified(variant, delayed)
    yl = u[3] if ylag is None else ylag
    args = list(np.asarray(u, float)) + [yl] + _param_values(model)
    J = np.array(f_J(*args), dtype=float)
    if delayed:
        return J, np.array(f_Jlag(*args), dtype=float).reshape(4, 1)
    return J


def symbolic_rhs(model: Model, u, ylag=None):
    variant = model.variant if model.rho > 0 else ROT_NONE
    f_rhs, _, _ = _lambdified(variant, False)
    yl = u[3] if ylag is None else ylag
    args = list(np.asarray(u, float)) + [yl] + _param_values(model)
    return np.array(f_rhs(*args), dtype=float).ravel()


def numeric_jacobian(model: Model, u, eps: float = 1e-7) -> np.ndarray:
    u = np.asarray(u, dtype=float)
    J = np.zeros((4, 4))
    for k in range(4):
        e = np.zeros(4)
        e[k] = eps
        J[:, k] = (reduced_rhs(model, u + e) - reduced_rhs(model, u - e)) / (2 * eps)
    return J


def in_domain(u, tol: float = 1e-9) -> bool:
    z = full_state(u)
    return bool(np.all(z[:4] >= -tol) and -tol <= z[4] <= 1 + tol)


def find_equilibria(model: Model, n_starts: int = 60, seed: int = 0, extra_starts=(),
                    tol: float = 1e-11):
    """Find equilibria in the domain by Newton-type root finding from many starts."""
    rng = np.random.default_rng(seed)
    starts = [np.asarray(s, float) for s in extra_starts]
    for _ in range(n_starts):
        x = rng.dirichlet(np.ones(4))
        starts.append(np.array([x[0], x[1], x[2], rng.uniform()]))
    found = []
    for s in starts:
        sol = root(lambda u: reduced_rhs(model, u), s, method="hybr", tol=tol)
        if not sol.success:
            continue
        u = sol.x
        if not in_domain(u) or np.max(np.abs(reduced_rhs(model, u))) > 1e-9:
            continue
        if all(np.max(np.abs(u - v)) > 1e-6 for v in found):
            found.append(u)
    return found


def refine_equilibrium(model: Model, u0, tol: float = 1e-12):
    sol = root(lambda u: reduced_rhs(model, u), np.asarray(u0, float), method="hybr", tol=tol)
    if not sol.success or not in_domain(sol.x):
        return None
    if np.max(np.abs(reduced_rhs(model, sol.x))) > 1e-9:
        return None
    return sol.x


def eigenvalues(model: Model, u) -> np.ndarray:
    ev = np.linalg.eigvals(jacobian(model, u))
    return ev[np.argsort(-ev.real)]


def leading_complex_real_part(ev) -> float:
    """Largest real part among eigenvalues with non-negligible imaginary part (nan if none)."""
    cplx = [e for e in ev if abs(e.imag) > 1e-9]
    return max(e.real for e in cplx) if cplx else float("nan")


def track_equilibrium(make_model, values, u_start):
    """Natural-parameter continuation of one equilibrium branch.

    make_model(v) -> Model. Returns arrays of (value, u, eigenvalues) for the tracked branch.
    """
    out = []
    u = np.asarray(u_start, float)
    for v in values:
        m = make_model(v)
        u_new = refine_equilibrium(m, u)
        if u_new is None:
            out.append((v, np.full(4, np.nan), np.full(4, np.nan + 0j)))
            continue
        u = u_new
        out.append((v, u.copy(), eigenvalues(m, u)))
    return out


def locate_hopf(make_model, lo, hi, u_guess, xtol: float = 1e-10):
    """Locate a Hopf point between lo and hi by bisection on the leading complex real part.

    Returns (value, u, imaginary part) or None if no sign change of a complex pair.
    """
    state = {"u": np.asarray(u_guess, float)}

    def g(v):
        m = make_model(v)
        u = refine_equilibrium(m, state["u"])
        if u is None:
            raise RuntimeError("lost equilibrium")
        state["u"] = u
        return leading_complex_real_part(eigenvalues(m, u))

    glo, ghi = g(lo), g(hi)
    if not (np.isfinite(glo) and np.isfinite(ghi)) or glo * ghi > 0:
        return None
    v = brentq(g, lo, hi, xtol=xtol)
    m = make_model(v)
    u = refine_equilibrium(m, state["u"])
    ev = eigenvalues(m, u)
    cplx = [e for e in ev if abs(e.imag) > 1e-9]
    lead = max(cplx, key=lambda e: e.real)
    return v, u, abs(lead.imag)


# ---------------------------------------------------------------------------
# Delay differential equations: characteristic roots via pseudospectral
# discretization of the infinitesimal generator (Chebyshev collocation).
# ---------------------------------------------------------------------------

def cheb(n: int):
    """Chebyshev differentiation matrix and nodes on [-1, 1] (Trefethen, Spectral Methods)."""
    if n == 0:
        return np.zeros((1, 1)), np.array([1.0])
    xg = np.cos(np.pi * np.arange(n + 1) / n)
    cvec = np.hstack([2.0, np.ones(n - 1), 2.0]) * (-1.0) ** np.arange(n + 1)
    X = np.tile(xg, (n + 1, 1)).T
    dX = X - X.T
    D = np.outer(cvec, 1.0 / cvec) / (dX + np.eye(n + 1))
    D = D - np.diag(D.sum(axis=1))
    return D, xg


def dde_char_roots(J0: np.ndarray, J1: np.ndarray, tau: float, n: int = 40) -> np.ndarray:
    """Approximate characteristic roots of x'(t) = J0 x(t) + J1 x(t - tau).

    Builds the (n+1) d x (n+1) d collocation matrix of the infinitesimal generator on Chebyshev
    nodes of [-tau, 0]; its rightmost eigenvalues converge spectrally to the rightmost
    characteristic roots. Returns eigenvalues sorted by decreasing real part.
    """
    d = J0.shape[0]
    if tau <= 0:
        return np.sort_complex(np.linalg.eigvals(J0 + J1))[::-1]
    D, xg = cheb(n)                      # nodes xg[0] = 1 (theta = 0), xg[n] = -1 (theta = -tau)
    D = D * (2.0 / tau)                  # map [-1, 1] -> [-tau, 0]
    A = np.zeros(((n + 1) * d, (n + 1) * d))
    A[:d, :d] = J0
    A[:d, n * d:(n + 1) * d] += J1
    for j in range(1, n + 1):
        for k in range(n + 1):
            A[j * d:(j + 1) * d, k * d:(k + 1) * d] = D[j, k] * np.eye(d)
    ev = np.linalg.eigvals(A)
    return ev[np.argsort(-ev.real)]
