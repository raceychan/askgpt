import typing as ty
from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class ErrorDetail:

    """
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
    --------
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
       }
    """

    # TODO: refactor to follow rfc-7807
    # type: skip, since problem page is not available
    # title: written in the class doc
    # detail: wrirten in the message Exception("detail")
    # instance: formed in the api response, include path

    error_code: str
    source: ty.Literal["server", "client"]
    description: str
    service: str
    message: str | tuple[ty.Any] = ""

    def asdict(self) -> dict[str, str]:
        return asdict(self)


class DomainError(Exception):
    "Uncaught domain error"

    description: str | None = None
    source: ty.Literal["server", "client"]
    service: str

    def __init__(self, message: str | None = None):
        super().__init__(message)
        self.message = message or ""
        self.detail = self._generate_detail()

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.detail.error_code}: {self.detail.message}>"

    def _generate_detail(self) -> ErrorDetail:
        desc = self.description or self.__doc__ or ""

        return ErrorDetail(
            error_code=self.__class__.__name__,
            description=desc.strip(),
            source=self.source,
            service=self.service,
            message=self.message,
        )


# class ServerSideError(DomainError):
#     source = "server"  # status > 500


class ClientSideError(DomainError):
    source = "client"  # 400 < status < 500
