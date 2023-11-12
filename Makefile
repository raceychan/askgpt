# #SHELL = /bin/zsh
# SHELL := /bin/zsh
# CONDA_ENV := askgpt

# .PHONY: shell
# shell:
# 	$(SHELL) conda activate $(CONDA_ENV)

.PHONY: test
test:
	pytest -sv --cov-report term-missing --cov=src tests/

.PHONY: debug
debug:
	pytest -svx --pdb tests/

.PHONY: typecheck
typecheck:
	mypy src/ --explicit-package-bases --enable-incomplete-feature=Unpack

.PHONY: setup
setup:
	poetry install
