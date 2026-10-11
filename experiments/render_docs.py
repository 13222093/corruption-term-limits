"""Render docs_src/*.md.in into the repository root, replacing {{Macro}} with the values in
paper/autogen_numbers.tex (R6: every number in the documents comes from results/).

Usage: python experiments/render_docs.py
"""
from __future__ import annotations

import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_macros():
    vals = {}
    pat = re.compile(r"^\\newcommand\{\\([A-Za-z]+)\}\{(.*)\}  % ")
    with open(os.path.join(ROOT, "paper", "autogen_numbers.tex"), encoding="utf-8") as fh:
        for line in fh:
            m = pat.match(line)
            if m:
                v = m.group(2)
                # LaTeX scientific notation -> plain text
                v = re.sub(r"\\times 10\^\{(-?\d+)\}", r"e\1", v)
                vals[m.group(1)] = v
    return vals


def main():
    vals = load_macros()
    missing = set()
    # Public templates render into the repository root. Author-only templates in private/docs_src/
    # (gitignored, not distributed) render into private/ when that folder is present.
    jobs = [(src, ROOT) for src in glob.glob(os.path.join(ROOT, "docs_src", "*.md.in"))]
    jobs += [(src, os.path.join(ROOT, "private"))
             for src in glob.glob(os.path.join(ROOT, "private", "docs_src", "*.md.in"))]
    for src, out_dir in jobs:
        with open(src, encoding="utf-8") as fh:
            text = fh.read()

        def rep(m):
            k = m.group(1)
            if k not in vals:
                missing.add(k)
                return m.group(0)
            return vals[k]
        def inc(m):
            with open(os.path.join(ROOT, m.group(1)), encoding="utf-8") as fh2:
                return fh2.read()
        text = re.sub(r"\{\{include:([^}]+)\}\}", inc, text)
        out = re.sub(r"\{\{([A-Za-z]+)\}\}", rep, text)
        dst = os.path.join(out_dir, os.path.basename(src)[:-3])
        rel_src = os.path.relpath(src, ROOT).replace(os.sep, "/")
        with open(dst, "w", encoding="utf-8") as fh:
            fh.write("<!-- Generated from " + rel_src
                     + " by experiments/render_docs.py; edit the template, not this file. -->\n"
                     + out)
        print("wrote", os.path.relpath(dst, ROOT))
    if missing:
        sys.exit(f"unknown macros: {sorted(missing)}")


if __name__ == "__main__":
    main()
