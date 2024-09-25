import typing as ty

from askgpt.helpers.error_registry import ErrorDetail

ErrorSource = ty.Literal["server", "client"]


class APPErrorBase(Exception):
    "domain error"

    description: str = ""
    source: ErrorSource = "client"
    service: str = ""

    def __init__(self, message: str = ""):
        super().__init__(message)
        self.message = message
        self.detail = self._generate_detail()

    def __repr__(self):
        return f"<{self.detail.error_code}: {self.detail.message}>"

    def _generate_detail(self) -> ErrorDetail:
        """
        generate error detail if description is provided or docstring is provided
        """
        desc = self.description or self.__doc__ or ""

        return ErrorDetail(
            error_code=self.__class__.__name__,
            description=desc.strip(),
            source=self.source,
            service=self.service,
            message=self.message,
        )


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
