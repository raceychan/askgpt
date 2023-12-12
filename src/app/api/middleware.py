from time import perf_counter
from urllib.parse import quote

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp, Receive, Scope, Send

from src.app.api.xheaders import XHeaders
from src.domain._log import logger
from src.domain.model.base import uuid_factory

MIN_PROCESS_TIME = 0.001  # 1ms


def request_id_factory() -> bytes:
    return uuid_factory().encode()


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


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    NOTE: we might want to implement our own ExceptionMiddleware here
    so that a consisten response with domain-defined x-headers always be returned
    whether the exception is raise or not
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        client_host, client_port = request.client or ("unknown_ip", "unknown_port")
        url_parts = request.url.components
        path_query = quote(
            "{}?{}".format(url_parts.path, url_parts.query)
            if url_parts.query
            else url_parts.path
        )

        request_id = request.headers[XHeaders.REQUEST_ID.value]
        with logger.contextualize(request_id=request_id):
            status_code = 500
            pre_process = perf_counter()
            try:
                response = await call_next(request)
                status_code = response.status_code
            except Exception as e:
                logger.exception("internal exception occurred")
                raise e
            finally:
                post_process = perf_counter()
                duration = max(round(post_process - pre_process, 3), MIN_PROCESS_TIME)
                logger.info(
                    f"""{client_host}:{client_port} - "{request.method} {path_query} HTTP/{request.scope["http_version"]}" {status_code}""",
                    duration=duration,
                )

            response.headers[XHeaders.REQUEST_ID.value] = request_id
            response.headers[XHeaders.PROCESS_TIME.value] = str(duration)
            return response
