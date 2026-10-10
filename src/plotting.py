"""Shared figure style. Strategy colors validated on all pairs (worst CVD Delta E 9.2,
normal-vision Delta E 16.3 on the light surface; checked with the dataviz
validator). Aqua sits below 3:1 contrast, so lines also carry line styles and
direct labels or legends (secondary encoding)."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e4e3df"

STRAT_COLORS = {"OC": "#2a78d6", "PC": "#1baf7a", "OD": "#eb6834", "PD": "#4a3aa7"}
STRAT_STYLES = {"OC": "-", "PC": "-", "OD": "--", "PD": "--"}
HONEST = "#2a78d6"
CORRUPT = "#e34948"
CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]

SEQ_BLUE = LinearSegmentedColormap.from_list(
    "seq_blue", ["#f4f8fe", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95",
                 "#0d366b"])
DIV_BR = LinearSegmentedColormap.from_list(
    "div_br", ["#c73a3a", "#e66767", "#f3b0ab", "#f0efec", "#9ec5f4", "#3987e5", "#184f95"])


def setup():
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "font.size": 9, "axes.titlesize": 9.5, "axes.labelsize": 9, "legend.fontsize": 8,
        "xtick.labelsize": 8, "ytick.labelsize": 8, "axes.edgecolor": INK2,
        "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2, "text.color": INK,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
        "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 1.6,
        "legend.frameon": False, "pdf.fonttype": 42, "ps.fonttype": 42,
        "font.family": "DejaVu Sans",
    })


def panel_label(ax, s):
    ax.text(-0.14, 1.04, s, transform=ax.transAxes, fontsize=11, fontweight="bold",
            va="bottom", ha="left", color=INK)


def save(fig, path_no_ext):
    fig.savefig(path_no_ext + ".png", dpi=200, bbox_inches="tight")
    fig.savefig(path_no_ext + ".pdf", bbox_inches="tight")
    plt.close(fig)
