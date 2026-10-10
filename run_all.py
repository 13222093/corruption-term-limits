"""Run the whole pipeline without make: python run_all.py [full|quick]"""
import subprocess
import sys

profile = sys.argv[1] if len(sys.argv) > 1 else "full"
steps = [
    [sys.executable, "-m", "pytest"],
    [sys.executable, "experiments/run_reproduction.py", profile],
    [sys.executable, "experiments/run_extension.py", profile],
    [sys.executable, "experiments/run_sensitivity.py", profile],
    [sys.executable, "experiments/evaluate_hypotheses.py", profile],
    [sys.executable, "experiments/make_figures.py", profile],
]
if profile == "full":
    steps += [[sys.executable, "experiments/make_numbers.py", profile],
              [sys.executable, "experiments/render_docs.py"],
              [sys.executable, "experiments/build_paper.py"]]
for cmd in steps:
    print(">>", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)
