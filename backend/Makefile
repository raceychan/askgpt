run := pixi run
app := askgpt

.PHONY: install
install:
	curl -fsSL https://pixi.sh/install.sh | bash
	pixi install

.PHONY: dev
dev:
	$(run) -e dev python -m $(app).server

.PHONY: stage
stage:
	$(run) -e dev gunicorn askgpt.api.app:app_factory  \
	--workers 1 -k uvicorn.workers.UvicornWorker \
	--bind 0.0.0.0:5000 --log-level critical

.PHONY: test
test:
	$(run) -e test pytest --durations=0 tests/ 

.PHONY: api_test
api_test:
	$(run) -e test python api_test.py

.PHONY: cov
cov:
	$(run) -e test pytest tests/ --cov=askgpt --cov-report term-missing 

.PHONY: debug
debug:
	$(run) pytest -vx --pdb tests/

.PHONY: openapi
openapi:
	$(run) python -m scripts.modify_openapi

.PHONY: logs
logs:
	docker logs -f $(app)

# DEVOPS 

.PHONY: gitlog
gitlog:
	git log --graph --oneline --decorate


.PHONY: typecheck
typecheck:
	mypy $(app)/ --explicit-package-bases --enable-incomplete-feature=Unpack


.PHONY: build
build:
	docker build -t $(app) .

.PHONY: stop
stop:
	docker stop $(app)

.PHONY: docker-clean
docker-clean:
	docker image prune -a -f

.PHONY: clean
clean:
	rm -rf .pytest_cache .mypy_cache .coverage .coverage.* .coverage* .pytest_cache .pyt

