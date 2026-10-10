"""Compile paper/main.tex with pdflatex + bibtex. Finds pdflatex on PATH or in the default
MiKTeX user install location."""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPER = os.path.join(ROOT, "paper")


def find(exe):
    p = shutil.which(exe)
    if p:
        return p
    cand = os.path.expandvars(rf"%LOCALAPPDATA%\Programs\MiKTeX\miktex\bin\x64\{exe}.exe")
    return cand if os.path.exists(cand) else None


def main():
    pdflatex, bibtex = find("pdflatex"), find("bibtex")
    if not pdflatex or not bibtex:
        sys.exit("pdflatex/bibtex not found. Install a TeX distribution (e.g. MiKTeX or TeX Live), "
                 "then run: cd paper && pdflatex main && bibtex main && pdflatex main && pdflatex main")
    run = lambda cmd: subprocess.run(cmd, cwd=PAPER, check=True, stdout=subprocess.DEVNULL)
    run([pdflatex, "-interaction=nonstopmode", "-halt-on-error", "main.tex"])
    run([bibtex, "main"])
    run([pdflatex, "-interaction=nonstopmode", "-halt-on-error", "main.tex"])
    run([pdflatex, "-interaction=nonstopmode", "-halt-on-error", "main.tex"])
    print("paper/main.pdf written")


if __name__ == "__main__":
    main()
