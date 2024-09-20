import json
from pathlib import Path

from askgpt.app.app import app_factory


def modify_openapi():
    openapi = app_factory().openapi()
    # TODO: process openapio
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

    content = json.dumps(_procecss_openapi(openapi))
    frontend_dir = Path.cwd().parent / "frontend"

    filepath = frontend_dir / "openapi.json"
    filepath.touch(exist_ok=True)
    filepath.write_text(content)


if __name__ == "__main__":
    modify_openapi()
