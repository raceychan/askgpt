from time import perf_counter
from urllib.parse import quote

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.middleware.cors import CORSMiddleware as CORSMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from askgpt.app.api.error_handlers import INTERNAL_ERROR_DETAIL, make_err_response
from askgpt.app.api.xheaders import XHeaders
from askgpt.domain.config import TIME_EPSILON_S, Settings, UnknownAddress
from askgpt.domain.model.base import request_id_factory
from askgpt.infra._log import logger


def log_request(request: Request, status_code: int, duration: float):
    client_host, client_port = request.client or UnknownAddress()
    url_parts = request.url.components
    path_query = quote(
        "{}?{}".format(url_parts.path, url_parts.query)
        if url_parts.query
        else url_parts.path
    )

    msg = f'{client_host}:{client_port} - "{request.method} {path_query} HTTP/{request.scope["http_version"]}" {status_code}'

    if status_code >= 400:
        logger.error(msg, duration=duration)
    else:
        logger.info(msg, duration=duration)


class TraceMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        # NOTE: remove follow three lines would break lifespan
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        x_request_id = XHeaders.REQUEST_ID.encoded
        if not (request_id := dict(scope["headers"]).get(x_request_id)):
            request_id = request_id_factory()
            scope["headers"].append((x_request_id, request_id))
        await self.app(scope, receive, send)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        request_id = request.headers[XHeaders.REQUEST_ID.value]
        with logger.contextualize(request_id=request_id):
            status_code = 500
            pre_process = perf_counter()
            try:
                response = await call_next(request)
                status_code = response.status_code
            except Exception as e:
                response = make_err_response(
                    request=request, error_detail=INTERNAL_ERROR_DETAIL, code=500
                )
                logger.exception(f"Internal exception {e} occurred")
                raise e from e
            else:
                response.headers[XHeaders.REQUEST_ID.value] = request_id
            finally:
                post_process = perf_counter()
                duration = max(round(post_process - pre_process, 3), TIME_EPSILON_S)
                response.headers[XHeaders.PROCESS_TIME.value] = str(duration)
                log_request(request, status_code, duration)
            return response


def add_middlewares(app: FastAPI, *, settings: Settings) -> None:
    """
    FILO
    """
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(TraceMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.security.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
