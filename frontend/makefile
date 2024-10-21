PROJECT_DIR := $(shell pwd)
# PROJECT_DIR := $(shell dirname $(shell pwd))


.PHONY: client
client:
	make -C ../backend openapi && \
	 npm run openapi-ts


# need to run backend/scripts/modify_openapi.py before this
.PHONY: dev
dev:
	make client
	npm run dev
