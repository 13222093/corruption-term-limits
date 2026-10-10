"""Compare pre-SI results (results/pre_si/) with the current full results and write
results/full/changes_si_table.md (included in CHANGES_SI.md by render_docs.py).

Old values come from results/pre_si/autogen_numbers_pre_si.tex and results/pre_si/hypotheses.json;
new values from paper/autogen_numbers.tex and results/full/hypotheses.json.
"""
from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import ROOT, RESULTS

PAT = re.compile(r"^\\newcommand\{\\([A-Za-z]+)\}\{(.*)\}  % (.*)$")

# Macros that depend on the individual-based model or the Markov chain (CHANGES_SI.md inventory).
FINITE_PREFIXES = ("Bthree", "EpisodesSteps", "Bfour", "LargeReps", "ValRms", "ValM", "Hone",
                   "Htwo", "Hthree", "HfourIncIBM", "HfourPairsIBM", "HfourYZero", "PulseIBM",
                   "Fin", "SE", "SLarge", "NeutralMaxDev", "Markov", "Nreps", "WinSmall",
                   "BurnSmall", "WinLarge", "BurnLarge", "MSmall", "NSmall")


def load(path):
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            m = PAT.match(line.rstrip("\n"))
            if m:
                out[m.group(1)] = (m.group(2), m.group(3))
    return out


def num(v):
    v = v.replace("\\times 10^{", "e").replace("}", "")
    try:
        return float(v)
    except ValueError:
        return None


def main():
    old = load(os.path.join(RESULTS, "pre_si", "autogen_numbers_pre_si.tex"))
    new = load(os.path.join(ROOT, "paper", "autogen_numbers.tex"))
    lines = ["| Quantity (macro) | Meaning | Old (pre-SI) | New (SI-verified) | Abs. change |",
             "|---|---|---|---|---|"]
    n_changed = 0
    n_fin = 0
    for name in sorted(old):
        if not name.startswith(FINITE_PREFIXES) or name.endswith(("Lo", "Hi")):
            continue
        if name not in new:
            continue
        n_fin += 1
        o, n = old[name][0], new[name][0]
        a, b = num(o), num(n)
        if a is not None and b is not None:
            ch = f"{abs(b - a):.3g}"
            changed = abs(b - a) > 0
        else:
            ch = "same" if o == n else "changed"
            changed = o != n
        n_changed += int(changed)
        lines.append(f"| `{name}` | {new[name][1]} | {o} | {n} | {ch} |")
    with open(os.path.join(RESULTS, "pre_si", "hypotheses.json")) as fh:
        ho = json.load(fh)["data"]
    with open(os.path.join(RESULTS, "full", "hypotheses.json")) as fh:
        hn = json.load(fh)["data"]
    hl = ["| Hypothesis | Old outcome | New outcome | Flipped? |", "|---|---|---|---|"]
    flips = 0
    for k in ("H1", "H2", "H3", "H4", "H5", "H6"):
        f = ho[k]["outcome"] != hn[k]["outcome"]
        flips += int(f)
        hl.append(f"| {k} | {ho[k]['outcome']} | {hn[k]['outcome']} | {'yes' if f else 'no'} |")
    new_only = sorted(set(new) - set(old))
    text = ["### Finite-population numbers", "",
            f"{n_fin} finite-population quantities compared; {n_changed} changed.", ""] + lines + [
            "", "### Hypothesis outcomes", "", f"{flips} of 6 outcomes changed.", ""] + hl + [
            "", "### New quantities added on this branch", "",
            ", ".join(f"`{n}`" for n in new_only if not n.endswith(("Lo", "Hi"))), ""]
    path = os.path.join(RESULTS, "full", "changes_si_table.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(text) + "\n")
    print(path, f"(finite {n_fin}, changed {n_changed}, flips {flips})")


if __name__ == "__main__":
    main()
