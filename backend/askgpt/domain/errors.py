import typing as ty

from askgpt.helpers.error_registry import RFC9457

ErrorSource = ty.Literal["server", "client"]


class GeneralAPPError(RFC9457):
    "Domain error"

    source: ErrorSource = "client"
    service: str = ""

    def __repr__(self):
        return f"<{self.error_detail}>"


class SystemNotSetError(GeneralAPPError): ...
