import typing as ty

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette import status
from starlette.responses import Response

from askgpt.api.errors import QuotaExceededError
from askgpt.api.xheaders import XHeaders
from askgpt.app.auth._errors import (
    AuthenticationError,
    UserAlreadyExistError,
    UserNotFoundError,
)
from askgpt.app.gpt._errors import (
    APIKeyNotAvailableError,
    APIKeyNotProvidedError,
    GPTError,
    OpenAIRequestError,
    OrphanSessionError,
)
from askgpt.domain.errors import EntityNotFoundError, GeneralWebError
from askgpt.helpers.error_registry import ErrorDetail, HandlerRegistry

handler_registry: ty.Final[HandlerRegistry] = HandlerRegistry()


class ServerResponse(Response):
    media_type = "application/json"


class ErrorResponse(JSONResponse):
    content: ErrorDetail
    headers: dict[str, str]  # type: ignore
    status_code: int

    def render(self, content: ErrorDetail) -> bytes:
        return content.model_dump_json().encode("utf-8")  # type: ignore


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
def _(request: Request, exc: GPTError) -> ErrorResponse:
    return make_err_response(
        request=request,
        code=status.HTTP_400_BAD_REQUEST,
        error_detail=exc.error_detail,
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


@handler_registry.register
def _(request: Request, exc: OpenAIRequestError) -> ErrorResponse:
    return make_err_response(
        request=request,
        code=exc.status_code,
        error_detail=exc.error_detail,
    )
