import inspect
import types
import typing as ty
from dataclasses import asdict, dataclass, field
from datetime import datetime

from fastapi import FastAPI, Request


def iso_now() -> str:
    return datetime.now().isoformat()


@dataclass(frozen=True, slots=True, kw_only=True)
class ErrorDetail:
    """
    RFC 9457
    ------
    https://www.rfc-editor.org/rfc/rfc9457.html


    RFC-7807
    ------
    https://datatracker.ietf.org/doc/html/rfc7807

    type: string
        A URI reference that identifies the problem type. Ideally, the URI should resolve to human-readable information describing the type, but that’s not necessary. The problem type provides information that’s more specific than the HTTP status code itself.
    title: string
        A human-readable description of the problem type, meaning that it should always be the same for the same type.
    status: number
        This reflects the HTTP status code and is a convenient way to make problem details self-contained. That way they can be interpreted outside of the context of the HTTP interaction in which they were provided.
    detail: string
        A human-readable description of the problem instance, explaining why the problem occurred in this specific case.
    instance: string
        A URI reference that identifies the problem instance. Ideally, the URI should resolve to information describing the problem instance, but that’s not necessary.

    Examples
    ------
    >>> response:
       HTTP/1.1 403 Forbidden
       Content-Type: application/problem+json
       Content-Language: en
       {
        "type": "https://example.com/probs/out-of-credit",
        "title": "You do not have enough credit.",
        "detail": "Your current balance is 30, but that costs 50.",
        "instance": "/account/12345/msgs/abc",
        "balance": 30,
        "accounts": ["/account/12345",
                     "/account/67890"]
        "timestamp": "2023-11-28T12:34:56Z",

       }

    TODO: refactor to follow rfc-7807
    type: skip, since problem page is not available, TODO: generate a problem page
    title: written in the class doc
    detail: wrirten in the message Exception("detail")
    instance: should be the id, say a user id, then we return /v1/user/{user_id}
    """

    error_code: str  # this should format a title, {service}-{className}
    source: ty.Literal["server", "client"]
    description: str  # should generate title
    service: str
    message: str | tuple[ty.Any]  # the "detail" field
    timestamp: str = field(default_factory=iso_now)

    def asdict(self) -> dict[str, str]:
        return asdict(self)


class IErrorResponse(ty.Protocol):
    detail: ErrorDetail
    headers: dict[str, str]
    status_code: int


type ExceptionHandler[Exc] = ty.Callable[[Request, Exc], IErrorResponse]


@ty.final
class HandlerRegistry[Exc: Exception]:
    """
    Add error handler to fastapi according to their signature
    """

    _handlers: dict[type[Exc] | int, ExceptionHandler[Exc]]

    def __init__(self):
        self._handlers = {}

    def __iter__(
        self,
    ) -> ty.Iterator[tuple[type[Exc] | int, ExceptionHandler[Exc]]]:
        return iter(self._handlers.items())

    @property
    def handlers(self):
        return self._handlers

    def register(self, handler: ExceptionHandler[Exc]) -> None:
        """\
        >>> @HandlerRegistry.register
        def any_error_handler(request: Request, exc: Exception | ty.Literal[500]) -> ErrorResponse:
        """
        exc_type = self._extract_exception(handler)
        exc_types = ty.get_args(exc_type)

        if exc_types:
            for exctype in exc_types:
                self._handlers[exctype] = handler
        else:
            exc_type = ty.cast(type[Exc] | int, exc_type)
            self._handlers[exc_type] = handler

    def inject_handlers(self, app: FastAPI) -> None:
        for exc, handler in self:
            app.add_exception_handler(exc, handler)  # type: ignore

    @classmethod
    def _extract_exception(
        cls, handler: ExceptionHandler[Exc]
    ) -> type[Exc] | int | types.UnionType | int:
        sig = inspect.signature(handler)
        _, exc = sig.parameters.values()
        exc_type = exc.annotation
        if exc_type is inspect._empty:  # type: ignore
            raise ValueError(f"handler {handler} has no annotation for {exc.name}")
        return exc_type


registry: ty.Final[HandlerRegistry] = HandlerRegistry[Exception]()
