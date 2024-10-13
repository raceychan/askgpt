import inspect
import types
import typing as ty
from string import Template

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from askgpt.helpers.functions import ClassAttr
from askgpt.helpers.string import str_to_kebab
from askgpt.helpers.time import iso_now

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
"""


class IErrorResponse(ty.Protocol):
    content: "ErrorDetail"
    headers: dict[str, str]
    status_code: int


type ExceptionHandler[Exc] = ty.Callable[[Request, Exc], IErrorResponse]


class ErrorDetail(BaseModel):
    """
    A RFC9457 compatible error detail
    """

    # To extend errordetail, create a subclass of ErrorDetail then set it to _error_detail
    type: str = Field(
        json_schema_extra={
            "title": "type",
            "description": "An URI that is used to locate the error type",
            "examples": ["https://example.com/errors?error_type=out-of-credit"],
        }
    )
    title: str = Field(
        json_schema_extra={
            "title": "title",
            "description": "A general description about why the problem would happen",
            "examples": ["You do not have enough credit."],
        }
    )
    detail: str | None = Field(
        default=None,
        json_schema_extra={
            "title": "detail",
            "description": "Detailed description of the problem instance",
            "examples": ["Your current balance is 30, but that costs 50."],
        },
    )
    status: int | None = Field(
        default=None,
        json_schema_extra={
            "title": "status",
            "description": "The standard http status code",
            "examples": ["500"],
        },
    )
    instance: str | None = Field(
        default=None,
        json_schema_extra={
            "title": "instance",
            "description": "An URI reference that identifies the problem instance or an entity_id",
            "examples": ["/account/12345/msgs/abc"],
        },
    )
    timestamp: str = Field(
        default_factory=iso_now,
        json_schema_extra={
            "title": "timestamp",
            "description": "Timestamp of which problem occured, in ISO format",
            "examples": ["YYYY-MM-DD HH:MM:SS.mmmmmm'"],
        },
    )
    request_id: str | None = Field(
        default=None,
        json_schema_extra={
            "title": "request_id",
            "description": "An uuid that is unique to each request, used for tracing",
            "examples": ["268388d5-d6c5-454c-976b-31ae864fcce4"],
        },
    )

    def model_dump_json(
        self, exclude_unset: bool = True, exclude_none: bool = True, **kwargs
    ):
        return super().model_dump_json(
            exclude_unset=exclude_unset, exclude_none=exclude_none
        )


class RFC9457(Exception):
    """
    To extend errordetail, create a subclass of ErrorDetail then set it to _error_detail
    """

    __error_type__: ClassAttr[str] | str = ClassAttr(
        lambda cls: str_to_kebab(cls.__name__)
    )
    __error_title__: ClassAttr[str] | str = ClassAttr(lambda cls: cls.__doc__ or "")

    def __init__(
        self,
        detail: str,
        *,
        type: str | None = None,
        title: str | None = None,
        instance: str | None = None,
        status: int | None = None,
        timestamp: str | None = None,
    ):

        self._error_detail = ErrorDetail(
            type=type or self.__class__.__error_type__,
            title=(title or self.__class__.__error_title__).strip(),
            detail=detail,
            instance=instance,
            status=status,
        )
        if timestamp:
            self._error_detail.timestamp = timestamp

    @property
    def error_detail(self) -> ErrorDetail:
        return self._error_detail

    @classmethod
    def static_error_detail(cls):
        return ErrorDetail(type=cls.__error_type__, title=cls.__error_title__)

    def to_json(self) -> str:
        return self.error_detail.model_dump_json()


class HandlerRegistry[Exc: Exception]:
    """
    Add error handler to fastapi according to their signature
    """

    _handlers: dict[type[Exc] | int, ExceptionHandler[Exc]]

    def __init__(self, error_route_path: str | None = None):
        self._handlers = {}
        self._error_route_path = error_route_path

    def __iter__(
        self,
    ) -> ty.Iterator[tuple[type[Exc] | int, ExceptionHandler[Exc]]]:
        return iter(self._handlers.items())

    @property
    def handlers(self):
        return self._handlers

    def register(self, handler: ExceptionHandler[Exc]) -> ExceptionHandler[Exc]:
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
        return handler

    def inject_handlers(self, app: FastAPI) -> None:
        if not self._handlers:
            raise Exception("Empty Exception Handler")
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


def error_route_factory(registry: HandlerRegistry, *, route_path: str = "/errors"):
    ERROR_TEMPLATE = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>API Errors Documentation</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            h1 {
                color: #2c3e50;
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
            }
            .error-box {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 20px;
                margin-bottom: 20px;
            }
            .error-title {
                font-size: 1.2em;
                color: #e74c3c;
                margin-bottom: 10px;
            }
            .error-field {
                margin-bottom: 10px;
            }
            .field-name {
                font-weight: bold;
                color: #2980b9;
            }
            .field-description {
                margin-left: 20px;
                font-style: italic;
            }
            .field-example {
                background-color: #ecf0f1;
                padding: 5px;
                border-radius: 3px;
                font-family: monospace;
                margin-left: 20px;
            }
        </style>
    </head>
    <body>
        <h1>API Errors Documentation</h1>
        $errors
    </body>
    </html>

    """

    def generate_error_page(error_type: str = "") -> str:
        doc = Template(ERROR_TEMPLATE)

        error_tmplt = """
        <div class="error-box">
            <div class="error-title">{title}</div>
            <span> (T, null) means a field will either be of type (T) or won't be returned.
            </span> 
            {fields}
        </div>
        """

        field_tmplt = """
        <div class="error-field">
            <span class="field-name">{name}({type}):</span>
            <span class="field-description">{description}</span>
            <div class="field-example">{value}</div>
        </div>
        """

        def format_field(field_info: dict[str, ty.Any], value: ty.Any) -> str:
            field_type = field_info.get("type", field_info.get("anyOf"))
            if isinstance(field_type, list):
                field_type = ty.cast(list[dict[str, str]], field_type)
                field_type = ", ".join([t["type"] for t in field_type])
            field_name = field_info.get("title")
            description = field_info.get("description")

            example = field_info.get("examples", [""])[0]
            value = value or example
            return field_tmplt.format(
                name=field_name,
                type=field_type,
                description=description,
                value=value,
            )

        def format_error(err: type[RFC9457]):
            error_detail = err.static_error_detail()
            schema = error_detail.model_json_schema()
            properties = schema.get("properties", {})

            fields_html: list[str] = []
            for field_name, field_info in properties.items():
                value = getattr(error_detail, field_name)
                fields_html.append(format_field(field_info, value))

            error_html = error_tmplt.format(
                title=err.__name__, fields="\n".join(fields_html)
            )
            return error_html

        errs = {
            exc
            for exc, _ in registry
            if (not isinstance(exc, int) and issubclass(exc, RFC9457))
        }
        if error_type:
            errs = {exc for exc in errs if exc.__error_type__ == error_type}

        errors_html = [format_error(err) for err in errs]
        errors = "\n".join(errors_html)
        final = doc.substitute(errors=errors)
        return final

    err_route = APIRouter()
    err_route.get(route_path, tags=[f"{route_path}"], response_class=HTMLResponse)(
        generate_error_page
    )
    return err_route
