project_name = askgpt

.PHONY: compose
compose:
	docker-compose up --build ${project_name} -d
