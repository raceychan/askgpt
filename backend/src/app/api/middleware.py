from time import perf_counter
from urllib.parse import quote

from fastapi import FastAPI, Request
from src.app.api.xheaders import XHeaders
from src.domain._log import logger
from src.domain.config import TIME_EPSILON_S, Settings, UnknownAddress
from src.domain.model.base import request_id_factory
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.middleware.cors import CORSMiddleware as CORSMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send


class TraceMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        # NOTE: remove follow three lines would break lifespan
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        x_request_id = XHeaders.REQUEST_ID.encoded
        request_id = dict(scope["headers"]).get(x_request_id, request_id_factory())
        scope["headers"].append((x_request_id, request_id))
        await self.app(scope, receive, send)


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


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    NOTE: we might want to implement our own ExceptionMiddleware here
    so that a consistent response with domain-defined x-headers will always be returned
    regardless of the exception is raise or not
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        request_id = request.headers[XHeaders.REQUEST_ID.value]
        with logger.contextualize(request_id=request_id):
            status_code = 500
            pre_process = perf_counter()
            try:
                response = await call_next(request)
                status_code = response.status_code
            except Exception as e:
                logger.exception(f"Internal exception {e} occurred")
                raise e
            finally:
                post_process = perf_counter()
                duration = max(round(post_process - pre_process, 3), TIME_EPSILON_S)
                response.headers[XHeaders.REQUEST_ID.value] = request_id
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
