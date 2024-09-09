import typing as ty
from urllib.parse import urlencode, urlunsplit

from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from fastapi.responses import StreamingResponse as StreamingResponse
from src.adapters.factory import adapter_locator
from starlette import status


class UrllibURL(ty.NamedTuple):
    scheme: str = ""
    netloc: str = ""
    url: str = ""
    query: str = ""
    fragment: str = ""


def redirect(
    route: APIRouter,
    *,
    path: str = "",
    query: ty.Mapping[str, str] | None = None,
    status_code: int = status.HTTP_303_SEE_OTHER,
):
    u = f"{adapter_locator.settings.api.API_VERSION_STR}{route.prefix}{path}"
    url = UrllibURL(url=u, query=urlencode(query) if query else "")
    rere = RedirectResponse(urlunsplit(url), status_code=status_code)
    return rere


class URLRouter:
    ...