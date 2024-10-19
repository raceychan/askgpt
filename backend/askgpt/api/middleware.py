import typing as ty
from time import perf_counter

from fastapi import Request
from fastapi.responses import Response

# from starlette.background import BackgroundTask
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.middleware.base import (
    _StreamingResponse as StreamingResponse,  # type: ignore
)
from starlette.middleware.cors import CORSMiddleware as CORSMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from askgpt.api.xheaders import XHeaders
from askgpt.domain.config import TIME_EPSILON_S, Settings
from askgpt.domain.model.base import request_id_factory
from askgpt.helpers._log import log_request, logger


class TraceMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        """
        Manipulate request scope to add request_id
        """
        # NOTE: remove follow three lines would break lifespan
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        x_request_id_key = XHeaders.REQUEST_ID.encoded
        if x_request_id_key not in dict(scope["headers"]):
            scope["headers"].append((x_request_id_key, request_id_factory()))

        await self.app(scope, receive, send)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        request_id = request.headers[XHeaders.REQUEST_ID.value]
        with logger.contextualize(request_id=request_id):
            pre_process = perf_counter()
            req_body = await request.body()
            response = await call_next(request)
            status_code = response.status_code
            res_body = b""

            # TODO: ignoer large stream file
            if status_code > 400:
                body_stream = ty.cast(StreamingResponse, response).body_iterator
                async for chunk in body_stream:
                    res_body += chunk  # type: ignore

                response = Response(
                    content=res_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type,
                    background=response.background,
                )

            duration = max(round(perf_counter() - pre_process, 3), TIME_EPSILON_S)
            response.headers[XHeaders.REQUEST_ID.value] = request_id
            response.headers[XHeaders.PROCESS_TIME.value] = str(duration)
            log_request(request, response, req_body, res_body, status_code, duration)
            return response


class ErrorResponseMiddleWare(BaseHTTPMiddleware):
    """
    ref: startlette/middleware/base.py
    BaseHTTPMiddleware.__calll_ would call the response.__call__ method,
    then pass (scope, wrapped_receive, send) to it
    so here what gets return does not matter
    as long as it is a response object
    """

    __DUMB_RESPONSE__ = Response()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        """
        we return a dummy response here in the first user defined middleware,
        so that our following middlewares can hanlde the response object without dealing with this.
        Exceptions would eventually be handled by the startlette ExceptionMiddleware,
        which uses our exception handlers to generate error response, so we don't need to worry about it here
        """
        try:
            resp = await call_next(request)
        except Exception as uncaught:
            """the servererror middleware provided by starlette would make sure only the Exception class itself,
            or subclasses of Exception that did not defined in the exception handlers would be raise here
            """
            return self.__DUMB_RESPONSE__
        return resp


def middlewares(*, settings: Settings) -> list[Middleware]:
    """
    Middleware Order:

    ServerErrorMiddleware: handle unhandled exception in app, return 500
    user_middleware: user defined middleware
    ExceptionMiddleware: handle exception in app with user defined handlers, return 4xx or 5xx
    """
    middlewares = [
        Middleware(
            CORSMiddleware,
            allow_origins=settings.security.CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        ),
        Middleware(ErrorResponseMiddleWare),
        Middleware(TraceMiddleware),
        Middleware(LoggingMiddleware),
    ]
    return middlewares
