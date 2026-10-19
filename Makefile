#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_NAME = us_housing_crisis_analysis
PYTHON_VERSION = 3.12
PYTHON_INTERPRETER = venv/bin/python

#################################################################################
# COMMANDS                                                                      #
#################################################################################


## Install Python dependencies
.PHONY: requirements
requirements:
	$(PYTHON_INTERPRETER) -m pip install -U pip
	$(PYTHON_INTERPRETER) -m pip install -e .
	



## Delete all compiled Python files
.PHONY: clean
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete


## Lint using ruff (use `make format` to do formatting)
.PHONY: lint
lint:
	$(PYTHON_INTERPRETER) -m ruff format --check
	$(PYTHON_INTERPRETER) -m ruff check

## Format source code with ruff
.PHONY: format
format:
	$(PYTHON_INTERPRETER) -m ruff check --fix
	$(PYTHON_INTERPRETER) -m ruff format







#################################################################################
# PROJECT RULES                                                                 #
#################################################################################


## Download and load every source into data/interim (and the geography reference files)
.PHONY: data
data:
	$(PYTHON_INTERPRETER) -c "from us_housing_crisis_analysis import geography; geography.download()"
	$(PYTHON_INTERPRETER) -m us_housing_crisis_analysis.dataset download
	$(PYTHON_INTERPRETER) -m us_housing_crisis_analysis.dataset load

## Build analysis panels into data/processed
.PHONY: features
features:
	$(PYTHON_INTERPRETER) -m us_housing_crisis_analysis.features

## Execute all notebooks in order
.PHONY: notebooks
notebooks:
	$(PYTHON_INTERPRETER) -m nbconvert --to notebook --execute --inplace --ExecutePreprocessor.kernel_name=python3 notebooks/*.ipynb

## Run all tests (data tests skip when data/ is not built)
.PHONY: test
test:
	$(PYTHON_INTERPRETER) -m pytest

## Run only tests that need no downloaded data and no long simulations
.PHONY: test-fast
test-fast:
	$(PYTHON_INTERPRETER) -m pytest -m "not data and not slow"

## Rebuild everything implemented so far
.PHONY: all
all: data features notebooks test


#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys; \
lines = '\n'.join([line for line in sys.stdin]); \
matches = re.findall(r'\n## (.*)\n[\s\S]+?\n([a-zA-Z_-]+):', lines); \
print('Available rules:\n'); \
print('\n'.join(['{:25}{}'.format(*reversed(match)) for match in matches]))
endef
export PRINT_HELP_PYSCRIPT

help:
	@$(PYTHON_INTERPRETER) -c "${PRINT_HELP_PYSCRIPT}" < $(MAKEFILE_LIST)
