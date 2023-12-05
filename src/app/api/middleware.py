from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp, Receive, Scope, Send

from src.app.api.xheaders import XHeaders
from src.domain._log import logger
from src.domain.model import uuid_factory


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

        with logger.contextualize(request_id=request_id):
            response = await call_next(request)
        return response
