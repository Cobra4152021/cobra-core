.PHONY: setup validate-env text-baseline siglip forward overfit dependence regression test lint

PYTHON ?= python

setup:
	$(PYTHON) -m pip install -U pip
	$(PYTHON) -m pip install -e "../kc001[dev]"
	$(PYTHON) -m pip install -e ".[dev]"

validate-env:
	$(PYTHON) -m cobra_kc002.cli validate-env

text-baseline:
	$(PYTHON) -m cobra_kc002.cli text-baseline

siglip:
	$(PYTHON) -m cobra_kc002.cli siglip

forward forward-gate:
	$(PYTHON) -m cobra_kc002.cli forward-gate

overfit:
	$(PYTHON) -m cobra_kc002.cli overfit

dependence:
	$(PYTHON) -m cobra_kc002.cli image-dependence

regression:
	$(PYTHON) -m cobra_kc002.cli text-regression

moe:
	$(PYTHON) -m cobra_kc002.cli moe-routing

test:
	$(PYTHON) -m pytest -q -m "not gpu and not real_weights"

test-gpu:
	$(PYTHON) -m pytest -q -m gpu

lint:
	ruff check src tests
