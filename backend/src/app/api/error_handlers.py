import inspect
import types
import typing as ty

from fastapi import FastAPI, Request
from src.app.api.errors import (
    APPError,
    EntityNotFoundError,
    ErrorDetail,
    QuotaExceededError,
)
from src.app.api.xheaders import XHeaders
from src.app.auth.errors import AuthenticationError
from src.app.gpt.errors import OrphanSessionError
from starlette import status
from starlette.background import BackgroundTask
from starlette.responses import JSONResponse, Response


class ServerResponse(Response):
    media_type = "application/json"


class ErrorResponse(JSONResponse):
    """
    Examples
    --------
    >>> response:
    {
        "type": "https://example.com/probs/out-of-credit",
        "title": "You do not have enough credit.",
        "detail": "Your current balance is 30, but that costs 50.",
        "instance": "/account/12345/msgs/abc",
        "balance": 30,
        "accounts": ["/account/12345",
                      "/account/67890"]
    }
    """

    def __init__(
        self,
        detail: ErrorDetail,
        request_id: str,
        headers: dict[str, str] | None = None,
        status_code: int = 500,
        background: BackgroundTask | None = None,
    ) -> None:
        content = dict(detail=detail.asdict())
        headers = {
            XHeaders.ERROR.value: detail.error_code,
            XHeaders.REQUEST_ID.value: request_id,
        } | (headers or {})

        content["detail"]["request_id"] = request_id

        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type=self.media_type,
            background=background,
        )


type ExceptionHandler[E] = ty.Callable[[Request, E], ErrorResponse]

@ty.final
class HandlerRegistry[Exc: Exception | int]:
    """
    Add error handler to fastapi according to their signature
    """

    __registry: dict[type[Exc] | int, ExceptionHandler[Exc]] = {}

    def __iter__(
        self,
    ) -> ty.Iterator[tuple[type[Exc] | int, ExceptionHandler[Exc]]]:
        return iter(self.__registry.items())

    @classmethod
    def register(cls, handler: ExceptionHandler[Exc]) -> None:
        """\
        >>> @HandlerRegistry.register
        def any_error_handler(request: Request, exc: Exception | ty.Literal[500]) -> ErrorResponse:
        """
        exc_type = cls.extra_exception_handler(handler)
        exc_types = ty.get_args(exc_type)

        if exc_types:
            for exctype in exc_types:
                cls.__registry[exctype] = handler
        else:
            exc_type = ty.cast(type[Exc] | int, exc_type)
            cls.__registry[exc_type] = handler

    @classmethod
    def extra_exception_handler(
        cls, handler: ExceptionHandler[Exc]
    ) -> type[Exc] | int | types.UnionType | int:
        sig = inspect.signature(handler)
        _, exc = sig.parameters.values()
        exc_type = exc.annotation
        if exc_type is inspect._empty:  # type: ignore
            raise ValueError(f"handler {handler} has no annotation for {exc.name}")
        return exc_type

    def inject_handlers(self, app: FastAPI) -> None:
        for exc, handler in self:
            app.add_exception_handler(exc, handler)  # type: ignore

@HandlerRegistry.register
def any_error_handler(request: Request, exc: Exception) -> ErrorResponse:
    # TODO: log error
    request_id = request.headers[XHeaders.REQUEST_ID.value]
    detail = ErrorDetail(
        error_code="InternalUnknownError",
        description="unknow error occured, please report with request id",
        source="server",
        service="unkown",
    )
    return ErrorResponse(
        detail=detail,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        request_id=request_id,
    )


@HandlerRegistry.register
def domain_error_handler(request: Request, exc: APPError) -> ErrorResponse:
    request_id = request.headers[XHeaders.REQUEST_ID.value]
    return ErrorResponse(
        detail=exc.detail,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        request_id=request_id,
    )


@HandlerRegistry.register
def authentication_error_handler(
    request: Request, exc: AuthenticationError
) -> ErrorResponse:
    request_id = request.headers[XHeaders.REQUEST_ID.value]
    return ErrorResponse(
        detail=exc.detail,
        status_code=status.HTTP_401_UNAUTHORIZED,
        request_id=request_id,
        headers={"WWW-Authenticate": "Bearer"},
    )


@HandlerRegistry.register
def entity_not_found_error_handler(
    request: Request, exc: EntityNotFoundError
) -> ErrorResponse:
    request_id = request.headers[XHeaders.REQUEST_ID.value]
    return ErrorResponse(
        detail=exc.detail,
        status_code=status.HTTP_404_NOT_FOUND,
        request_id=request_id,
        headers={"WWW-Authenticate": "Bearer"},
    )


@HandlerRegistry.register
def orphan_session_error_handler(request: Request, exc: OrphanSessionError):
    request_id = request.headers[XHeaders.REQUEST_ID.value]
    return ErrorResponse(
        detail=exc.detail,
        status_code=status.HTTP_403_FORBIDDEN,
        request_id=request_id,
    )


@HandlerRegistry.register
def quota_exceeded_error_handler(request: Request, exc: QuotaExceededError):
    request_id = request.headers[XHeaders.REQUEST_ID.value]
    return ErrorResponse(
        detail=exc.detail,
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        request_id=request_id,
    )

def add_exception_handlers(app: FastAPI) -> None:
    registry: HandlerRegistry[Exception] = HandlerRegistry()
    registry.inject_handlers(app)