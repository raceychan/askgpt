# from enum import Enum

# from starlette import status

# from src.app.error import ErrorDetail


# class DomainException(Exception):
#     detail: ErrorDetail = ErrorDetail(
#         error_code="UNKOWN_DOMAIN_ERROR",
#         description="uncaught domain error",
#         source="server",
#     )
#     http_code: int = 500
#     headers: dict[str, str] = {"X-Error": detail.error_code}

#     def __init__(
#         self,
#         detail: ErrorDetail | None = None,
#         http_code: int | None = None,
#         headers: dict[str, str] | None = None,
#     ):
#         self.detail = detail or self.detail
#         self.http_code = http_code or self.http_code

#         if headers:
#             self.headers.update(headers)

#     def __repr__(self):
#         return f"<{self.__class__.__name__} {self.detail.error_code}: {self.detail.message}>"


# class DomainErrors(str, Enum):
#     def __init__(self, error: str, desc: str, status: int):
#         self.error = error
#         self.desc = desc
#         self.status = status

#     UncaughtDomainError = ("UncaughtDomainError", "Uncaught domain error", 500)
#     InvalidAuthError = ("InvalidAuthError", "Invalid authentication", 401)
#     UserNotFoundError = ("UserNotFoundError", "User not found", 404)


# class ErrorResponse:
#     error: DomainErrors


# class AuthenticationError(DomainException):
#     http_code = status.HTTP_401_UNAUTHORIZED
#     headers = DomainException.headers | {"X-Error": "Authentication Error"}


# class InvalidAuthError(AuthenticationError):
#     detail = ErrorDetail(
#         error_code="Invalid Authentication",
#         description="Incorrect username or password",
#         source="auth",
#     )
#     headers = AuthenticationError.headers | {"WWW-Authenticate": "Bearer"}


# class UserNotFoundError(AuthenticationError):
#     detail = ErrorDetail(
#         error_code="User not found",
#         description="User not found",
#         source="auth",
#     )
#     http_code = status.HTTP_404_NOT_FOUND
#     headers = AuthenticationError.headers | {"WWW-Authenticate": "Bearer"}
