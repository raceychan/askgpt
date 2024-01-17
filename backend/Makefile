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
install:
	curl -fsSL https://pixi.sh/install.sh | bash
	pixi install

.PHONY: shell
shell:
	pixi shell

.PHONY: server
server:
	python -m src.server

.PHONY: build
build:
	docker build -t askgpt .

.PHONY: run
run:
	docker run -p 8000:8000 askgpt

.PHONY:
clean:
	rm -rf .pytest_cache .mypy_cache .coverage .coverage.* .coverage* .pytest_cache .pyt

