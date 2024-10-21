PROJECT_NAME := askgpt
PROJECT_DIR := $(shell pwd)

.PHONY: compose
compose:
	docker compose up --build ${PROJECT_NAME}
