from time import perf_counter

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp, Receive, Scope, Send

from src.app.api.xheaders import XHeaders
from src.domain._log import logger
from src.domain.model import uuid_factory

MIN_PROCESS_TIME = 0.001  # 1ms


def request_id_factory() -> bytes:
    return uuid_factory().encode()


class TraceMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = request_id_factory()
        scope["headers"].append((XHeaders.REQUEST_ID.lower().encode(), request_id))
        await self.app(scope, receive, send)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        request_id = request.headers[XHeaders.REQUEST_ID]

        client_host, client_port = request.client or ("unknown_ip", "unknown_port")
        http_method = request.method
        http_version = request.scope["http_version"]
        url_parts = request.url.components
        if url_parts.query == "":
            path_query = url_parts.path
        else:
            path_query = "{}?{}".format(url_parts.path, url_parts.query)

        with logger.contextualize(request_id=request_id):
            status_code = 500
            pre_process = perf_counter()
            try:
                response = await call_next(request)
            except Exception as e:
                raise e
            else:
                status_code = response.status_code
            finally:
                post_process = perf_counter()
                duration = max(round(post_process - pre_process, 3), MIN_PROCESS_TIME)
                logger.info(
                    f"""{client_host}:{client_port} - "{http_method} {path_query} HTTP/{http_version}" {status_code}""",
                    request_id=request_id,
                    method=request.method,
                    path=request.url.path,
                    duration=duration,
                )
        response.headers[XHeaders.PROCESS_TIME] = str(duration)
        return response
