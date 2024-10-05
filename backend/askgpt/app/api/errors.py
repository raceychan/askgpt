import typing as ty

from askgpt.helpers.error_registry import RFC9457

ErrorSource = ty.Literal["server", "client"]


class APPErrorBase(RFC9457):
    "Domain error"

    source: ErrorSource = "client"
    service: str = ""

    def __repr__(self):
        return f"<{self._error_detail.title}: {self.error_detail.detail}>"


class EntityNotFoundError(APPErrorBase):
    "Entity not found"


class ThrottlingError(APPErrorBase):
    "Request throttled"


class QuotaExceededError(ThrottlingError):
    "Request quota exceeded"

    def __init__(self, quota: int, wait_time: float):
        self.quota = quota
        self.wait_time = wait_time
        super().__init__(
            f"Quota exceeded, next request available in {wait_time} seconds"
        )
