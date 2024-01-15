from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from starlette import status

from src.adapters.factory import AdapterRegistry


def redirect(
    route: APIRouter, entity_id: str, status_code: int = status.HTTP_303_SEE_OTHER
):
    api_str = AdapterRegistry.settings.api.API_VERSION_STR
    resp = RedirectResponse(
        f"{api_str}{route.prefix}?email={entity_id}", status_code=status_code
    )
    return resp
