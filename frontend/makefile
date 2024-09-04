.PHONY: openapi
openapi:
	@curl -s "http://localhost:5000/v1/openapi.json" | \
	jq '.paths |= map_values(map_values(.tags as $$tags | .operationId |= sub("^(\\($$tags[0]\\))-";"") ))' \
	> openapi.json
	@echo "OpenAPI specification updated in openapi.json"

.PHONY: client
client:
	npm run openapi-ts


.PHONY: dev
dev:
	make client
	npm run dev
