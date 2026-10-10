"""Model parameters and the admissibility inequalities of Lee et al. (2019).

Source: Lee, Iwasa, Dieckmann, Sigmund, PNAS 116:13276 (2019).
- Base values b, c, f, B, h, A: Fig. 1 caption (p.13278).
- Inequalities 1-4: main text p.13277, right column, Eqs. [1]-[4].
- Exploration rates and population sizes: Fig. 1 and Fig. 3 captions.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import math

# Strategy indices (Methods p.13280: order OC, PC, OD, PD).
OC, PC, OD, PD = 0, 1, 2, 3
STRATEGIES = ("OC", "PC", "OD", "PD")
# Umpire types: index 0 honest (H), 1 corrupt (C).
H, C = 0, 1


@dataclass(frozen=True)
class Params:
    """Game and learning parameters. Defaults are the base values of Fig. 1 (p.13278)."""

    b: float = 1.0      # benefit of donation (Fig. 1 caption)
    c: float = 0.5      # cost of donation (Fig. 1 caption)
    f: float = 0.2      # fee paid to the umpire (Fig. 1 caption)
    B: float = 0.2      # bribe paid by a defector to a corrupt umpire (Fig. 1 caption)
    h: float = 0.1      # cost of information for prudent players (Fig. 1 caption)
    A: float = 2.0      # fine imposed by an honest umpire (Fig. 1 caption)
    mu: float = 1e-4    # player exploration rate (Fig. 3 orange orbit, mean field)
    nu: float = 1e-4    # umpire exploration rate (Fig. 3: mu = nu)

    def with_(self, **kw) -> "Params":
        return replace(self, **kw)

    def as_dict(self) -> dict:
        return asdict(self)


def inequalities(p: Params) -> dict:
    """Return each admissibility inequality (Eqs. 1-4, p.13277) as (lhs, rhs, holds)."""
    out = {
        "eq1_f+h<b-c": (p.f + p.h, p.b - p.c),
        "eq2_c+h<A": (p.c + p.h, p.A),
        "eq3_B+h<c": (p.B + p.h, p.c),
        "eq4_h<sqrt(f(f+B))": (p.h, math.sqrt(p.f * (p.f + p.B))),
    }
    return {k: (lhs, rhs, lhs < rhs) for k, (lhs, rhs) in out.items()}


def check_inequalities(p: Params) -> bool:
    """True if all four inequalities of the paper hold (also requires h > 0, Methods p.13281)."""
    return p.h > 0 and all(v[2] for v in inequalities(p).values())


# Individual-based settings from the Fig. 1 caption (p.13278).
SMALL_IBM = dict(M=50, N=10, mu=0.001, nu=0.005, s=1e10)     # Fig. 1 A, B: sustained cycles
LARGE_IBM = dict(M=5000, N=1000, mu=0.01, nu=0.05, s=0.3)    # Fig. 1 C, D: damped oscillations

# Fig. 3 caption (p.13279): initial state and exploration rates mu = nu.
FIG3_X0 = (0.1, 0.4, 0.4, 0.1)
FIG3_Y0 = 1.0
FIG3_RATES = (1e-4, 0.02, 0.07)
