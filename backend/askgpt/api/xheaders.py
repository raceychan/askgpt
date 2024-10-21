from enum import StrEnum


class XHeaders(StrEnum):
    REQUEST_ID = "X-Request-ID"
    ERROR = "X-Error"
    PROCESS_TIME = "X-Process-Time"

    @property
    def encoded(self) -> bytes:
        return self.value.encode()

    @property
    def value(self) -> str:
        return self._value_.lower()
