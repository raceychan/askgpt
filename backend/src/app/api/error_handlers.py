from fastapi import Request
from fastapi.responses import JSONResponse
from src.app.api.errors import (
    APPError,
    EntityNotFoundError,
    ErrorDetail,
    QuotaExceededError,
)
from src.app.api.xheaders import XHeaders
from src.app.auth.errors import AuthenticationError, UserNotFoundError
from src.app.gpt.errors import OrphanSessionError
from src.helpers.error_handlers import ErrorDetail, registry
from starlette import status
from starlette.background import BackgroundTask
from starlette.responses import Response


class ServerResponse(Response):
    media_type = "application/json"


class ErrorResponse(JSONResponse):
    headers: dict[str, str]
    detail: ErrorDetail
    status_code: int

    def __init__(
        self,
        detail: ErrorDetail,
        headers: dict[str, str],
        status_code: int = 500,
        background: BackgroundTask | None = None,
    ) -> None:
        content = dict(detail=detail.asdict())

        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type=self.media_type,
            background=background,
        )


def make_err_response(
    *,
    request_id: str,
    detail: ErrorDetail,
    code: int,
    headers: dict[str, str] | None = None
) -> ErrorResponse:
    default_headers = {
        XHeaders.ERROR.value: detail.error_code,
        XHeaders.REQUEST_ID.value: request_id,
    }
    headers = default_headers | (headers or {})
    return ErrorResponse(
        detail=detail,
        status_code=code,
        headers=headers,
    )


@registry.register
def _any_error_handler(request: Request, exc: Exception) -> ErrorResponse:
    # TODO: log error
    request_id = request.headers[XHeaders.REQUEST_ID.value]
    detail = ErrorDetail(
        error_code="InternalUnknownError",
        description="unknow error occured, please report with request id",
        message="something went wrong",
        source="server",
        service="unkown",
    )
    return make_err_response(
        request_id=request_id, detail=detail, code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


@registry.register
def _domain_error_handler(request: Request, exc: APPError) -> ErrorResponse:
    request_id = request.headers[XHeaders.REQUEST_ID.value]
    return make_err_response(
        request_id=request_id,
        detail=exc.detail,
        code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@registry.register
def _authentication_error_handler(
    request: Request, exc: AuthenticationError
) -> ErrorResponse:
    request_id = request.headers[XHeaders.REQUEST_ID.value]
    return make_err_response(
        request_id=request_id,
        detail=exc.detail,
        code=status.HTTP_401_UNAUTHORIZED,
        headers={"WWW-Authenticate": "Bearer"},
    )


@registry.register
def _user_notfound_error_handler(request: Request, exc: UserNotFoundError):
    request_id = request.headers[XHeaders.REQUEST_ID.value]
    return make_err_response(
        detail=exc.detail,
        code=status.HTTP_404_NOT_FOUND,
        request_id=request_id,
        headers={"WWW-Authenticate": "Bearer"},
    )


@registry.register
def _entity_not_found_error_handler(
    request: Request, exc: EntityNotFoundError
) -> ErrorResponse:
    request_id = request.headers[XHeaders.REQUEST_ID.value]
    return make_err_response(
        detail=exc.detail,
        code=status.HTTP_404_NOT_FOUND,
        request_id=request_id,
        headers={"WWW-Authenticate": "Bearer"},
    )


@registry.register
def _orphan_session_error_handler(request: Request, exc: OrphanSessionError):
    request_id = request.headers[XHeaders.REQUEST_ID.value]
    return make_err_response(
        detail=exc.detail,
        code=status.HTTP_403_FORBIDDEN,
        request_id=request_id,
    )


@registry.register
def _quota_exceeded_error_handler(request: Request, exc: QuotaExceededError):
    request_id = request.headers[XHeaders.REQUEST_ID.value]
    return make_err_response(
        detail=exc.detail,
        code=status.HTTP_429_TOO_MANY_REQUESTS,
        request_id=request_id,
    )
