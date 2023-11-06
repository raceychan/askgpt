.PHONY: test
test:
	pytest -sv --cov-report term-missing --cov=src tests/

.PHONY: typecheck
typecheck:
	mypy src/ --explicit-package-bases

.PHONY: setup
setup:
	poetry install
