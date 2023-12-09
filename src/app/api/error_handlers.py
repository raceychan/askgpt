import inspect
import types
import typing as ty

from fastapi import Request
from pydantic import ValidationError
from starlette.background import BackgroundTask
from starlette.responses import JSONResponse, Response

from src.app.api.xheaders import XHeaders
from src.app.auth.service import (  # InvalidPasswordError,; UserNotFoundError,
    AuthenticationError,
)
from src.app.error import DomainError, ErrorDetail

# from src.domain._log import logger


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

        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type=self.media_type,
            background=background,
        )


type ExceptionHandler[E] = ty.Callable[[Request, E], ErrorResponse]


class HandlerRegistry[E: Exception | int]:
    """
    add error handler to fastapi according to their signature
    """

    _registry: dict[E, ExceptionHandler[E]] = {}

    @classmethod
    def register(cls, handler: ExceptionHandler[E]) -> None:
        exc_type = cls.extra_exception_handler(handler)
        tp_args = ty.get_args(exc_type)
        if tp_args:
            for t in tp_args:
                t = ty.cast(E, t)
                cls._registry[t] = handler
        else:
            exc_type = ty.cast(E, exc_type)
            cls._registry[exc_type] = handler

    @classmethod
    def extra_exception_handler(
        cls, handler: ExceptionHandler[E]
    ) -> E | types.UnionType:
        sig = inspect.signature(handler)

        params = [p for p in sig.parameters.values()]
        exc_type = params[1].annotation
        if exc_type is inspect._empty:  # type: ignore
            raise ValueError
        return exc_type

    def __iter__(
        self,
    ) -> ty.Iterator[tuple[E, ExceptionHandler[E]]]:
        return iter(self._registry.items())


@HandlerRegistry.register
def any_error_handler(request: Request, exc: Exception) -> ErrorResponse:
    # TODO: log error
    request_id = request.headers[XHeaders.REQUEST_ID.value]
    detail = ErrorDetail(
        error_code="InternalUnknownError",
        description="unknow error occured, please report",
        source="server",
        service="unkown",
    )
    return ErrorResponse(
        detail=detail,
        status_code=500,
        request_id=request_id,
    )


@HandlerRegistry.register
def domain_error_handler(request: Request, exc: DomainError) -> ErrorResponse:
    request_id = request.headers[XHeaders.REQUEST_ID.value]
    return ErrorResponse(
        detail=exc.detail,
        status_code=500,
        request_id=request_id,
    )


@HandlerRegistry.register
def domain_data_validation_error(
    request: Request, exc: ValidationError
) -> ErrorResponse:
    request_id = request.headers[XHeaders.REQUEST_ID.value]

    detail = ErrorDetail(
        error_code="DomainDataValidationError",
        description="unkown data validation error",
        source="server",
        service="domain",
        message="",
    )

    return ErrorResponse(
        detail=detail,
        status_code=500,
        request_id=request_id,
    )


@HandlerRegistry.register
def authentication_error_handler(
    request: Request, exc: AuthenticationError
) -> ErrorResponse:
    request_id = request.headers[XHeaders.REQUEST_ID.value]
    return ErrorResponse(
        detail=exc.detail,
        status_code=401,
        request_id=request_id,
    )
