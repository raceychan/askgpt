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

.PHONY: install
setup:
	pixi install

.PHONY: shell
shell:
	pixi shell

