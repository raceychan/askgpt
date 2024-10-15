import typing as ty

from askgpt.helpers.error_registry import RFC9457

ErrorSource = ty.Literal["server", "client"]


class GeneralAPPError(Exception):
    """Any Error throw by this app should be subclasses of this.
    For any error that should be returned to client, use GeneralWebError.
    NOTE: Do not catch error caused by coding.
    """


class StaticAPPError(GeneralAPPError):
    """Raised when a error only happends at import time,
    like settings error, import error, etc.
    This is to remind developer what the error is.
    """


class UnreachableResourceError(GeneralAPPError):
    """
    Raised when a resource(db, message queue, etc.) is not reachable.
    """


class GeneralWebError(GeneralAPPError, RFC9457):
    """
    The basic error classes that contains RFC9457 compatible error detail.
    NOTE: this error should only be used for errors shoudld be returned to api-client.
    """

    source: ErrorSource = "client"
    service: str = ""

    def __repr__(self):
        return f"<{self.error_detail}>"


class SystemNotSetError(GeneralWebError): ...
