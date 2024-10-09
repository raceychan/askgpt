import typing as ty

from askgpt.helpers.error_registry import RFC9457

ErrorSource = ty.Literal["server", "client"]


class GeneralAPPError(Exception):
    """Any Error throw by this app should be subclasses of this"""

    ...


class StaticAPPError(GeneralAPPError):
    """Error that happends before app runs, like settings error, import error, etc."""


class GeneralWebError(GeneralAPPError, RFC9457):
    "Domain error"

    source: ErrorSource = "client"
    service: str = ""

    def __repr__(self):
        return f"<{self.error_detail}>"


class SystemNotSetError(GeneralWebError): ...
