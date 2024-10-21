import json
from pathlib import Path

from askgpt.api.app import app_factory

FRONTEND_DIR = Path.cwd().parent / "frontend"
OPENAPI_PATH = FRONTEND_DIR / "openapi.json"


def _procecss_openapi(openapi: dict):
    for path_data in openapi["paths"].values():
        for operation in path_data.values():
            tags = operation.get("tags", [])
            if not tags:
                continue
            tag = operation["tags"][0]
            operation_id: str = operation["operationId"]
            operation.update(operationId=operation_id.removeprefix(f"{tag}-"))
    return openapi


def modify_openapi():
    openapi = app_factory().openapi()
    content = json.dumps(_procecss_openapi(openapi))
    OPENAPI_PATH.touch(exist_ok=True)
    OPENAPI_PATH.write_text(content)


if __name__ == "__main__":
    modify_openapi()
