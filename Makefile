# This file is originally from
# https://github.com/python-poetry/poetry

# Licensed under the MIT license:
# http://www.opensource.org/licenses/MIT-license
# Copyright (c) 2018 Sébastien Eustace

RELEASE := $$(sed -n -E "s/__version__ = '(.+)'/\1/p" src/cr_kyoushi/simulation/__version__.py)
PY_SRC := src/ tests/

# lists all available targets
list:
	@sh -c "$(MAKE) -p no_targets__ | \
		awk -F':' '/^[a-zA-Z0-9][^\$$#\/\\t=]*:([^=]|$$)/ {\
			split(\$$1,A,/ /);for(i in A)print A[i]\
		}' | grep -v '__\$$' | grep -v 'make\[1\]' | grep -v 'Makefile' | sort"
# required for list
no_targets__:

clean:
	@rm -rf build dist .eggs *.egg-info
	@rm -rf .benchmarks .coverage coverage.xml htmlcov report.xml .tox
	@find . -type d -name '.mypy_cache' -exec rm -rf {} +
	@find . -type d -name '__pycache__' -exec rm -rf {} +
	@find . -type d -name '*pytest_cache*' -exec rm -rf {} +
	@find . -type f -name "*.py[co]" -exec rm -rf {} +

# install all dependencies
setup: setup-python

# test your application (tests in the tests/ directory)
test:
	@poetry run pytest --cov=src/cr_kyoushi --cov-config .coveragerc --cov-report xml --cov-report term tests/ -sq

test-html:
	@poetry run pytest --cov=src/cr_kyoushi --cov-config .coveragerc --cov-report html --cov-report term tests/ -sq

release: build

build:
	@poetry build

publish:
	@poetry publish

wheel:
	@poetry build -v

# run tests against all supported python versions
tox:
	@tox

# quality checks
check: check-black check-flake8 check-isort check-safety  ## Check it all!

check-black:  ## Check if code is formatted nicely using black.
	@poetry run black --check $(PY_SRC)

check-flake8:  ## Check for general warnings in code using flake8.
	@poetry run flake8 $(PY_SRC)

check-isort:  ## Check if imports are correctly ordered using isort.
	@poetry run isort -c $(PY_SRC)

check-pylint:  ## Check for code smells using pylint.
	@poetry run pylint $(PY_SRC)

check-safety:  ## Check for vulnerabilities in dependencies using safety.
	@poetry run pip freeze 2>/dev/null | \
		grep -v cr_kyoushi.simulation | \
		poetry run safety check --stdin --full-report 2>/dev/null

# linting/formating
format: clean lint-black lint-isort

lint-black:  ## Lint the code using black.
	@poetry run black $(PY_SRC)

lint-isort:  ## Sort the imports using isort.
	@poetry run isort $(PY_SRC)
