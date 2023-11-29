from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class AccessToken:
    expire_at: datetime
    user_id: str

    def asdict(self):
        return asdict(self)
