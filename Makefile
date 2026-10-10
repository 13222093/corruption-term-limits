# Regenerate everything: make all  (on Windows: mingw32-make all)
# PROFILE=quick for a fast pipeline check, PROFILE=full for the reported numbers.
PYTHON ?= python
PROFILE ?= full

.PHONY: all test reproduce extension sensitivity hypotheses figures numbers docs paper quick clean

all: test reproduce extension sensitivity hypotheses figures numbers docs paper

test:
	$(PYTHON) -m pytest

reproduce:
	$(PYTHON) experiments/digitize_si.py $(PROFILE)
	$(PYTHON) experiments/run_reproduction.py $(PROFILE)

extension:
	$(PYTHON) experiments/run_extension.py $(PROFILE)

sensitivity:
	$(PYTHON) experiments/run_sensitivity.py $(PROFILE)

hypotheses:
	$(PYTHON) experiments/evaluate_hypotheses.py $(PROFILE)

figures:
	$(PYTHON) experiments/make_figures.py $(PROFILE)

numbers:
	$(PYTHON) experiments/make_numbers.py $(PROFILE)

docs: numbers
	$(PYTHON) experiments/make_changes_si.py
	$(PYTHON) experiments/render_docs.py

paper: numbers
	$(PYTHON) experiments/build_paper.py

quick:
	$(MAKE) test reproduce extension sensitivity hypotheses figures PROFILE=quick

clean:
	$(PYTHON) -c "import shutil; [shutil.rmtree(p, ignore_errors=True) for p in (\"results/quick\", \"figures/quick\")]"
