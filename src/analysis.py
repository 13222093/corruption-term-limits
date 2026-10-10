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


def locate_hopf(make_model, lo, hi, u_guess, xtol: float = 1e-10, n_scan: int = 60,
                log_scan: bool = None):
    """Locate the Hopf point closest to hi in [lo, hi].

    The equilibrium is continued from hi towards lo on a scan grid (log-spaced if lo > 0 and
    hi / lo > 20), the first sign change of the real part of the leading complex pair is
    bracketed, and refined by Brent's method. u_guess must be the equilibrium near hi.
    Returns (value, u, |imaginary part|) or None if no sign change of a complex pair.
    """
    if log_scan is None:
        log_scan = lo > 0 and hi / lo > 20
    grid = np.geomspace(hi, lo, n_scan) if log_scan else np.linspace(hi, lo, n_scan)
    branch = track_equilibrium(make_model, grid, u_guess)
    vals = [(v, u, leading_complex_real_part(ev), int(np.sum(np.real(ev) > 0)))
            for v, u, ev in branch]
    bracket = None
    for (v1, u1, g1, n1), (v2, u2, g2, n2) in zip(vals[:-1], vals[1:]):
        # genuine Hopf: a complex pair crosses (n_unstable changes by 2)
        if np.isfinite(g1) and np.isfinite(g2) and g1 * g2 < 0 and abs(n1 - n2) == 2:
            bracket = (v2, v1, u1)
            break
    if bracket is None:
        return None
    a, b, u_b = bracket
    state = {"u": np.asarray(u_b, float)}

    def g(v):
        m = make_model(v)
        u = refine_equilibrium(m, state["u"])
        if u is None:
            raise RuntimeError("lost equilibrium")
        state["u"] = u
        return leading_complex_real_part(eigenvalues(m, u))

    v = brentq(g, a, b, xtol=xtol)
    m = make_model(v)
    u = refine_equilibrium(m, state["u"])
    ev = eigenvalues(m, u)
    cplx = [e for e in ev if abs(e.imag) > 1e-9]
    lead = max(cplx, key=lambda e: e.real)
    return v, u, abs(lead.imag)


# ---------------------------------------------------------------------------
# Near-closed-form approximation of the critical rotation rate (author's
# derivation; verified against continuation in tests and results).
# ---------------------------------------------------------------------------

def invasion_thresholds(p: Params):
    """Honest fractions below which OD and PD can invade a population of OCs (mu -> 0).

    OD - OC payoff at the OC vertex: c - B - y (A - B)  -> y_OD = (c - B) / (A - B).
    PD - OC payoff at the OC vertex: (c - B - h) - y (b - f - B) -> y_PD = (c - B - h)/(b - f - B).
    These are the two ratios in the Fig. 3 caption of Lee et al.
    """
    return (p.c - p.B) / (p.A - p.B), (p.c - p.B - p.h) / (p.b - p.f - p.B)


def _G_honest(y, p: Params, p0: float = 1.0):
    """Rotation rate that makes honest fraction y an equilibrium near the OC vertex.

    Mutation-selection balance near x = (1, 0, 0, 0): a rare type j has frequency
    x_j = mu / (3 d_j(y)), with payoff deficits relative to OC
      d_PC = (1 - y)(b - c - f) + h,  d_OD = y (A - B) - (c - B),  d_PD = y (b - f - B) - (c - B - h).
    To first order in x_j, P_H - P_C = 4 f (x2 - x4) - 2 B (x3 + x4). The umpire equation
    y (1 - y)(P_H - P_C) + nu (1 - 2 y) + rho (p0 - y) = 0 then gives rho = G(y).
    """
    dPC = (1 - y) * (p.b - p.c - p.f) + p.h
    dOD = y * (p.A - p.B) - (p.c - p.B)
    dPD = y * (p.b - p.f - p.B) - (p.c - p.B - p.h)
    x2, x3, x4 = p.mu / (3 * dPC), p.mu / (3 * dOD), p.mu / (3 * dPD)
    dP = 4 * p.f * (x2 - x4) - 2 * p.B * (x3 + x4)
    return -(y * (1 - y) * dP + p.nu * (1 - 2 * y)) / (p0 - y)


def rho_c_approx(p: Params, p0: float = 1.0):
    """Approximate critical rotation rate (fold that creates the honest equilibrium).

    rho_c ~ min_{y > y_th} G(y), y_th = max(y_OD, y_PD). G is linear in (mu, nu), so rho_c is
    proportional to the exploration rates. Returns (rho_c, y at the fold).
    """
    from scipy.optimize import minimize_scalar
    y_th = max(invasion_thresholds(p))
    r = minimize_scalar(lambda y: _G_honest(y, p, p0), bounds=(y_th + 1e-9, p0 - 1e-6),
                        method="bounded", options={"xatol": 1e-10})
    return float(r.fun), float(r.x)


# ---------------------------------------------------------------------------
# Pseudo-arclength continuation of equilibria in one parameter, with fold and
# Hopf detection (R2: "numerical continuation").
# ---------------------------------------------------------------------------

def _F(make_model, w):
    return reduced_rhs(make_model(w[4]), w[:4])


def _Fw(make_model, w, eps: float = 1e-7):
    m = make_model(w[4])
    Ju = jacobian(m, w[:4])
    Fl = (_F(make_model, np.r_[w[:4], w[4] + eps]) - _F(make_model, np.r_[w[:4], w[4] - eps]))
    return np.hstack([Ju, (Fl / (2 * eps)).reshape(4, 1)])


def _tangent(A, t_prev=None):
    _, _, Vt = np.linalg.svd(A)
    t = Vt[-1]
    if t_prev is not None and t @ t_prev < 0:
        t = -t
    return t / np.linalg.norm(t)


def continue_equilibria(make_model, u0, lam0, lam_min, lam_max, ds: float = 1e-3,
                        ds_min: float = 1e-7, ds_max: float = 2e-2, max_steps: int = 20000,
                        direction: int = 1):
    """Pseudo-arclength continuation of F(u, lam) = 0 starting at (u0, lam0).

    Returns a dict of arrays: lam, u (n x 4), stable (bool), lead (leading eigenvalue),
    fold_idx and hopf_idx (indices after which a fold / Hopf was detected).
    """
    w = np.r_[np.asarray(u0, float), lam0]
    A = _Fw(make_model, w)
    t = _tangent(A)
    if np.sign(t[4]) != np.sign(direction):
        t = -t
    pts, stab, lead = [w.copy()], [], []
    ev = eigenvalues(make_model(w[4]), w[:4])
    stab.append(bool(ev[0].real < 0))
    lead.append(ev[0])
    n_unst = [int(np.sum(ev.real > 0))]
    folds, hopfs = [], []
    for _ in range(max_steps):
        ok = False
        while ds >= ds_min:
            wp = w + ds * t
            wc = wp.copy()
            for _it in range(12):
                Fv = _F(make_model, wc)
                G = np.r_[Fv, t @ (wc - wp)]
                Jg = np.vstack([_Fw(make_model, wc), t])
                dw = np.linalg.solve(Jg, -G)
                wc = wc + dw
                if np.max(np.abs(dw)) < 1e-11:
                    break
            if np.max(np.abs(_F(make_model, wc))) < 1e-9 and np.linalg.norm(wc - w) < 3 * ds:
                ok = True
                break
            ds *= 0.5
        if not ok:
            break
        t_new = _tangent(_Fw(make_model, wc), t)
        if t_new[4] * t[4] < 0:
            folds.append(len(pts) - 1)
        w, t = wc, t_new
        if not in_domain(w[:4], tol=1e-6) or not (lam_min <= w[4] <= lam_max):
            break
        pts.append(w.copy())
        ev = eigenvalues(make_model(w[4]), w[:4])
        stab.append(bool(ev[0].real < 0))
        lead.append(ev[0])
        n_u = int(np.sum(ev.real > 0))
        # Hopf: the number of unstable eigenvalues changes by 2 and a complex pair is involved
        # (a focus turning into a node changes the leading complex pair but not n_unstable).
        if abs(n_u - n_unst[-1]) == 2 and (np.any(np.abs(ev.imag) > 1e-9)
                                          or np.any(np.abs(lead[-2].imag) > 1e-9)):
            hopfs.append(len(pts) - 2)
        n_unst.append(n_u)
        ds = min(ds * 1.3, ds_max)
    P = np.array(pts)
    return {"lam": P[:, 4], "u": P[:, :4], "stable": np.array(stab), "lead": np.array(lead),
            "fold_idx": folds, "hopf_idx": hopfs}


def refine_hopf(make_model, u_guess, lam_guess):
    """Solve F(u, lam) = 0 and Re(leading complex eigenvalue pair) = 0 for a Hopf point.

    Works near folds where natural-parameter continuation fails. Returns (lam, u, omega).
    """
    def G(w):
        if not np.all(np.isfinite(w)):
            return np.full(5, 1e3)
        m = make_model(w[4])
        g = leading_complex_real_part(eigenvalues(m, w[:4]))
        if not np.isfinite(g):  # no complex pair at this trial point: push the solver back
            g = 1.0
        return np.r_[reduced_rhs(m, w[:4]), g]
    sol = root(G, np.r_[u_guess, lam_guess], method="hybr", tol=1e-13)
    if not sol.success or np.max(np.abs(G(sol.x))) > 1e-9:
        return None
    ev = eigenvalues(make_model(sol.x[4]), sol.x[:4])
    omega = max(abs(e.imag) for e in ev if abs(e.real) < 1e-6 and abs(e.imag) > 1e-9)
    return sol.x[4], sol.x[:4], omega


def refine_fold(make_model, u_guess, lam_guess):
    """Solve F(u, lam) = 0 and det J_u = 0 for a fold point."""
    def G(w):
        m = make_model(w[4])
        return np.r_[reduced_rhs(m, w[:4]), np.linalg.det(jacobian(m, w[:4])) * 1e4]
    sol = root(G, np.r_[u_guess, lam_guess], method="hybr", tol=1e-13)
    if not sol.success:
        return None
    return sol.x[4], sol.x[:4]


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
