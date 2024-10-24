from askgpt.domain.errors import GeneralWebError


class ThrottlingError(GeneralWebError):
    "Request throttled"


class QuotaExceededError(ThrottlingError):
    "Request quota exceeded"

    def __init__(self, quota: int, wait_time: float):
        self.quota = quota
        self.wait_time = wait_time
        super().__init__(
            f"Quota exceeded, next request available in {wait_time} seconds"
        )
