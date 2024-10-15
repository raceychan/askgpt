import typing as ty

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette import status
from starlette.responses import Response

from askgpt.api.errors import EntityNotFoundError, GeneralWebError, QuotaExceededError
from askgpt.api.xheaders import XHeaders
from askgpt.feat.auth.errors import (
    AuthenticationError,
    UserAlreadyExistError,
    UserNotFoundError,
)
from askgpt.feat.gpt.errors import (
    APIKeyNotAvailableError,
    APIKeyNotProvidedError,
    OrphanSessionError,
)
from askgpt.helpers.error_registry import ErrorDetail, HandlerRegistry

# BUG? (pylance), if we defined generic var lhs of =, it would be contravariant, otherwise it would be covariant
handler_registry: ty.Final[HandlerRegistry[GeneralWebError]] = HandlerRegistry()


class ServerResponse(Response):
    media_type = "application/json"


class ErrorResponse(JSONResponse):
    content: ErrorDetail
    headers: dict[str, str]
    status_code: int

    def render(self, content: ErrorDetail) -> bytes:
        content.model_json_schema()
        return content.model_dump_json().encode("utf-8")


INTERNAL_ERROR_DETAIL = ErrorDetail(
    type="InternalUnknownError",
    title="Unknow error occured, please report with request id",
    detail="something went wrong",
)


def make_err_response(
    *,
    request: Request,
    error_detail: ErrorDetail,
    code: int,
    headers: dict[str, str] | None = None,
) -> ErrorResponse:
    request_id = request.headers[XHeaders.REQUEST_ID.value]
    default_headers = {
        XHeaders.ERROR.value: error_detail.type,
        XHeaders.REQUEST_ID.value: request_id,
    }
    headers = default_headers | (headers or {})
    error_detail.request_id = request_id
    return ErrorResponse(
        content=error_detail,
        status_code=code,
        headers=headers,
    )


@handler_registry.register
def _(request: Request, exc: Exception) -> ErrorResponse:
    return make_err_response(
        request=request,
        error_detail=INTERNAL_ERROR_DETAIL,
        code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@handler_registry.register
def _(request: Request, exc: GeneralWebError) -> ErrorResponse:
    return make_err_response(
        request=request,
        error_detail=exc.error_detail,
        code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


# it seems HandlerRegistry is a Contravarience, but it should be a Covariance
@handler_registry.register
def _(request: Request, exc: AuthenticationError) -> ErrorResponse:
    return make_err_response(
        request=request,
        error_detail=exc.error_detail,
        code=status.HTTP_401_UNAUTHORIZED,
        headers={"WWW-Authenticate": "Bearer"},
    )


@handler_registry.register
def _(request: Request, exc: UserNotFoundError) -> ErrorResponse:
    return make_err_response(
        request=request,
        error_detail=exc.error_detail,
        code=status.HTTP_404_NOT_FOUND,
        headers={"WWW-Authenticate": "Bearer"},
    )


@handler_registry.register
def _(request: Request, exc: UserAlreadyExistError) -> ErrorResponse:
    return make_err_response(
        request=request,
        error_detail=exc.error_detail,
        code=status.HTTP_409_CONFLICT,
        headers={"WWW-Authenticate": "Bearer"},
    )


@handler_registry.register
def _(request: Request, exc: EntityNotFoundError) -> ErrorResponse:
    return make_err_response(
        request=request,
        code=status.HTTP_404_NOT_FOUND,
        error_detail=exc.error_detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


@handler_registry.register
def _(request: Request, exc: OrphanSessionError) -> ErrorResponse:
    return make_err_response(
        request=request,
        code=status.HTTP_403_FORBIDDEN,
        error_detail=exc.error_detail,
    )


@handler_registry.register
def _(request: Request, exc: APIKeyNotProvidedError) -> ErrorResponse:
    return make_err_response(
        request=request,
        code=status.HTTP_403_FORBIDDEN,
        error_detail=exc.error_detail,
    )


@handler_registry.register
def _(request: Request, exc: APIKeyNotAvailableError) -> ErrorResponse:
    return make_err_response(
        request=request,
        code=status.HTTP_400_BAD_REQUEST,
        error_detail=exc.error_detail,
    )


@handler_registry.register
def _(request: Request, exc: QuotaExceededError) -> ErrorResponse:
    return make_err_response(
        request=request,
        code=status.HTTP_429_TOO_MANY_REQUESTS,
        error_detail=exc.error_detail,
    )


def add_exception_handlers(app: "FastAPI") -> None:
    if not handler_registry.handlers:
        raise Exception("Empty error handler registry")
    handler_registry.inject_handlers(app)
