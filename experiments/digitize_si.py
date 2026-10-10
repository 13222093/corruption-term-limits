"""Digitize read-offs from the SI of Lee et al. (2019) (refs/pnas.1900078116.sapp.pdf).

1. SI Fig. 8 (page 8): number of strategy cycles in each player panel over 5 x 10^6 time units.
   The figure is vector graphics. Each panel is rendered at 1200 dpi inside its plot frame and
   one line is traced by its color:
   - s = 10 panels (A, D, G): spikes of the prudent-defector line (yellow, RGB 224 227 40),
     counted with hysteresis (top of the line above 35% of the axis, then below 8%); the
     optimistic-defector line (brown) is counted the same way (above 12%, below 3%) as a check.
   - s = 1 panels (B, E, H): the optimistic-cooperator line (teal, RGB 22 130 128), mean height
     per pixel column, counted with hysteresis 0.7 / 0.3.
   - s = 0.3 panels (C, F, I) show no regular cycles and are not counted.
   Frame boxes were located on a 300-dpi rendering (dark frame lines) and are stored below.
2. SI Fig. 9B (page 9): positions of the printed period labels, read from a 150-dpi rendering
   and converted to (h, mu) with the caption's axes (h horizontal 0-0.35, mu = nu vertical
   0-0.08; notation inconsistency D7: the panel labels are exchanged). Contour labels sit on their contour
   lines, so the period at each position is approximately the label value.

Usage: python experiments/digitize_si.py [profile]  ->  results/<profile>/si_digitized.json
"""
from __future__ import annotations

import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from src.utils import ROOT, load_config, save_result

SI = os.path.join(ROOT, "refs", "pnas.1900078116.sapp.pdf")

# plot frames of the player panels on page 8, in pixels of a 300-dpi rendering
FRAMES = {"A": (396, 820, 438, 677), "D": (396, 820, 1163, 1401), "G": (396, 820, 1888, 2126),
          "B": (1016, 1440, 438, 677), "E": (1016, 1440, 1163, 1401),
          "H": (1016, 1440, 1888, 2126)}
SETTINGS = {"A": (3000, 10.0), "D": (2000, 10.0), "G": (1000, 10.0),
            "B": (3000, 1.0), "E": (2000, 1.0), "H": (1000, 1.0)}
YELLOW, BROWN, TEAL = (224, 227, 40), (131, 68, 27), (22, 130, 128)

# SI Fig. 9B label positions at 150 dpi: (label, x_px, y_px); plot box x: h = 0 at 746,
# h = 0.35 at 1083; y: mu = 0 at 523, mu = 0.08 at 184 (read from the rendered page).
FIG9B_LABELS = [(100, 798, 346), (120, 800, 396), (150, 813, 446), (200, 851, 483),
                (300, 889, 499), (400, 930, 506), (90, 801, 312), (80, 808, 279)]
FIG9B_BOX = {"x0": 746, "x1": 1083, "y0": 523, "y1": 184, "hmax": 0.35, "mumax": 0.08}


def hysteresis_count(v, hi, lo):
    state, n = None, 0
    for a in v:
        if a > hi:
            if state == "low":
                n += 1
            state = "high"
        elif a < lo:
            state = "low"
    return n


def panel(page, key, dpi=1200):
    import fitz
    x0, x1, y0, y1 = FRAMES[key]
    pt = lambda v: v / 300 * 72  # noqa: E731
    pix = page.get_pixmap(dpi=dpi, clip=fitz.Rect(pt(x0 + 3), pt(y0 + 2), pt(x1 - 3), pt(y1 - 2)))
    return np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width,
                                                              pix.n)[:, :, :3].astype(int)


def line_top(img, color):
    m = np.abs(img - np.array(color)).sum(axis=2) < 60
    H = img.shape[0]
    return np.array([(1 - np.where(m[:, c])[0].min() / H) if m[:, c].any() else 0.0
                     for c in range(m.shape[1])])


def line_mean(img, color):
    m = np.abs(img - np.array(color)).sum(axis=2) < 60
    H = img.shape[0]
    return np.array([(1 - np.where(m[:, c])[0].mean() / H) if m[:, c].any() else np.nan
                     for c in range(m.shape[1])])


def digitize_fig8():
    import fitz
    doc = fitz.open(SI)
    page = doc[7]
    out = {}
    for key, (M, s) in SETTINGS.items():
        img = panel(page, key)
        if s >= 10:
            pd_n = hysteresis_count(line_top(img, YELLOW), 0.35, 0.08)
            od_n = hysteresis_count(line_top(img, BROWN), 0.12, 0.03)
            out[key] = {"M": M, "N": M // 5, "s": s, "cycles": pd_n, "cycles_check_OD": od_n,
                        "method": "PD spikes (0.35/0.08)"}
        else:
            lev = line_mean(img, TEAL)
            n = hysteresis_count(lev[~np.isnan(lev)], 0.7, 0.3)
            out[key] = {"M": M, "N": M // 5, "s": s, "cycles": n,
                        "method": "OC hysteresis (0.7/0.3)"}
    return out


def fig9b_points():
    b = FIG9B_BOX
    pts = []
    for lab, x, y in FIG9B_LABELS:
        h = (x - b["x0"]) / (b["x1"] - b["x0"]) * b["hmax"]
        mu = (b["y0"] - y) / (b["y0"] - b["y1"]) * b["mumax"]
        pts.append({"label_period": lab, "h": round(h, 4), "mu": round(mu, 4)})
    return pts


def main(profile="full"):
    cfg = load_config(profile)
    if not os.path.exists(SI):
        # refs/ is not distributed (copyright). The read-offs do not depend on the profile, so a
        # clone without the SI reuses the committed results/full/si_digitized.json.
        src = os.path.join(ROOT, "results", "full", "si_digitized.json")
        dst = os.path.join(ROOT, "results", profile, "si_digitized.json")
        print(f"SI PDF not found at {os.path.relpath(SI, ROOT)}; using committed read-offs "
              f"in {os.path.relpath(src, ROOT)}")
        if os.path.abspath(src) != os.path.abspath(dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
        return
    data = {"source": "refs/pnas.1900078116.sapp.pdf", "fig8": digitize_fig8(),
            "fig9b_label_points": fig9b_points(),
            "note": "Read-offs from SI figures; approximate (see module docstring)."}
    print(save_result("si_digitized", data, cfg))
    for k, v in data["fig8"].items():
        print(k, v)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "full")
