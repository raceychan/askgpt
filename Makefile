.PHONY: gitlog
gitlog:
	git log --graph --oneline --decorate

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
	conda install -c conda-forge poetry=1.7.0
	poetry install --no-root
