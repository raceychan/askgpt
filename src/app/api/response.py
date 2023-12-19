from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from starlette import status

from src.domain.config import get_setting


def redirect(
    route: APIRouter, entity_id: str, status_code: int = status.HTTP_303_SEE_OTHER
):
    api_str = get_setting().api.API_VERSION_STR
    resp = RedirectResponse(
        f"{api_str}{route.prefix}/{entity_id}", status_code=status_code
    )
    breakpoint()
    return resp
