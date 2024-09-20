run := pixi run

.PHONY: install
install:
	curl -fsSL https://pixi.sh/install.sh | bash
	pixi install


.PHONY: dev
dev:
	$(run) python -m askgpt.server --config dev.settings.toml

.PHONY: test
test:
	$(run) -e test pytest -sv --cov-report term-missing --cov=askgpt tests/

.PHONY: debug
debug:
	$(run) pytest -svx --pdb tests/

.PHONY: openapi
openapi:
	$(run) python -m scripts.modify_openapi

# DEVOPS 

.PHONY: gitlog
gitlog:
	git log --graph --oneline --decorate


.PHONY: typecheck
typecheck:
	mypy askgpt/ --explicit-package-bases --enable-incomplete-feature=Unpack


.PHONY: build
build:
	docker build -t askgpt .

.PHONY: run
run:
	docker run -p 8000:8000 askgpt

.PHONY: stop
stop:
	docker stop askgpt

.PHONY: docker-clean
docker-clean:
	docker image prune -a -f

.PHONY: clean
clean:
	rm -rf .pytest_cache .mypy_cache .coverage .coverage.* .coverage* .pytest_cache .pyt



