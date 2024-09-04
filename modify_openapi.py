import json
from pathlib import Path

from backend.src.app.app import app_factory


def modify():
    openapi = app_factory().openapi()
    # TODO: process openapio
    for path_data in openapi["paths"].values():
        for operation in path_data.values():
            tag = operation["tags"][0]
            operation_id: str = operation["operationId"]
            operation.update(operationId=operation_id.removeprefix(f"{tag}-"))

    filepath = Path("frontend/openapi.json")
    filepath.write_text(json.dumps(openapi))


if __name__ == "__main__":
    modify()
