# PROJECT_DIR := $(shell pwd)
PROJECT_DIR := $(shell dirname $(shell pwd))


.PHONY: client
client:
	cd $(PROJECT_DIR)/backend && \
	 pixi run python scripts/modify_openapi.py && \
	 cd $(PROJECT_DIR)/frontend && \
	 npm run openapi-ts


# need to run backend/scripts/modify_openapi.py before this
.PHONY: dev
dev:
	make client
	npm run dev
