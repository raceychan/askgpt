import typing as ty
from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class ErrorDetail:
    error_code: str
    source: ty.Literal["server", "client"]
    description: str
    service: str
    message: str | None = None

    def asdict(self) -> dict[str, str]:
        return asdict(self)


class DomainError(Exception):
    "Uncaught domain error"

    description: str | None = None
    source: ty.Literal["server", "client"]
    service: str

    def __init__(self, message: str | None = None):
        super().__init__(message)
        self.message = message
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


class ServerSideError(DomainError):
    source = "server"


class ClientSideError(DomainError):
    source = "client"
