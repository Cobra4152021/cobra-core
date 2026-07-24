.PHONY: setup validate-env smoke-text smoke-vision test overfit image-dependence lint

PYTHON ?= python
PIP ?= pip

setup:
	$(PIP) install -U pip
	$(PIP) install -e ".[dev]"
	@echo "Optional QLoRA: pip install -e \".[qlora]\""

validate-env:
	$(PYTHON) -m cobra_kc001.cli validate-env

smoke-text:
	$(PYTHON) -m cobra_kc001.cli smoke-text

smoke-vision:
	$(PYTHON) -m cobra_kc001.cli smoke-vision

test:
	$(PYTHON) -m pytest -q

overfit:
	$(PYTHON) -m cobra_kc001.cli overfit

image-dependence:
	$(PYTHON) -m cobra_kc001.cli image-dependence

lint:
	ruff check src tests
