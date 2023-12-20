import functools
import pathlib
import typing as ty
from functools import lru_cache

from pydantic import BaseModel, ConfigDict

from src.domain.interface import SQL_ISOLATIONLEVEL, EventLogRef, JournalRef, SystemRef
from src.infra.fileutil import FileUtil


class SettingsFactory[T](ty.Protocol):
    def __call__(self, settings: "Settings") -> T:
        ...


def settingfactory[T: ty.Any](factory: SettingsFactory[T]) -> SettingsFactory[T]:
    return lru_cache(maxsize=1)(factory)


class TimeScale:
    "A more type-aware approach to time scale"
    Second = ty.NewType("Second", int)
    Minute = ty.NewType("Minute", int)
    Hour = ty.NewType("Hour", int)
    Day = ty.NewType("Day", int)
    Week = ty.NewType("Week", int)


UNIT = MINUTE = 1
HOUR = 60 * MINUTE
DAY = 24 * HOUR
WEEK = 7 * DAY


class SettingsBase(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        use_enum_values=True,
        validate_default=True,
        strict=False,
        extra="forbid",
    )


class Settings(SettingsBase):
    PROJECT_NAME: ty.ClassVar[str] = "askgpt"
    PROJECT_ROOT: ty.ClassVar[pathlib.Path] = pathlib.Path.cwd()

    RUNTIME_ENV: ty.Literal["dev", "prod", "test"]

    # make pyright happy, Settings is hashable by setting frozen=True
    __hash__: ty.Callable[[None], int]

    @property
    def is_prod_env(self):
        return self.RUNTIME_ENV == "prod"

    class DB(SettingsBase):
        DB_DRIVER: str = "sqlite"
        ASYNC_DB_DRIVER: str = "aiosqlite"
        DATABASE: pathlib.Path
        ISOLATION_LEVEL: SQL_ISOLATIONLEVEL = "SERIALIZABLE"
        ENGINE_ECHO: bool = False

        USER: str = ""
        PASSWORD: str = ""
        HOST: str = ""
        PORT: str = ""

        @property
        def DB_URL(self) -> str:
            base = f"{self.DB_DRIVER}://"
            if self.USER and self.PASSWORD:
                base += f"{self.USER}:{self.PASSWORD}"
            elif self.USER:
                base += self.USER
            elif self.PASSWORD:
                raise ValueError("Password without user is not allowed")

            if self.HOST:
                base += f"@{self.HOST}"
            if self.PORT:
                base += f":{self.PORT}"
            if self.DATABASE:
                base += f"/{self.DATABASE}"
            return base

        @property
        def ASYNC_DB_URL(self) -> str:
            return self.DB_URL.replace(
                self.DB_DRIVER, f"{self.DB_DRIVER}+{self.ASYNC_DB_DRIVER}", 1
            )

    db: DB

    class ActorRefs(SettingsBase):
        SYSTEM: SystemRef = SystemRef("system")
        EVENTLOG: EventLogRef = EventLogRef("eventlog")
        JOURNAL: JournalRef = JournalRef("journal")

    actor_refs: ActorRefs

    class Security(SettingsBase):
        SECRET_KEY: str  # 32 bytes url safe string
        ALGORITHM: str  # jose.constants.ALGORITHMS
        ACCESS_TOKEN_EXPIRE_MINUTES: TimeScale.Minute = TimeScale.Minute(WEEK)

    security: Security

    class API(SettingsBase):
        HOST: str
        PORT: int
        API_VERSION: str = "1"

        @property
        def API_VERSION_STR(self) -> str:
            return f"/v{self.API_VERSION}"

        @property
        def OPEN_API(self) -> str:
            return f"{self.API_VERSION_STR}/openapi.json"

        @property
        def DOCS(self) -> str:
            return f"{self.API_VERSION_STR}/docs"

        @property
        def REDOC(self) -> str:
            return f"{self.API_VERSION_STR}/redoc"

    api: API

    class Redis(SettingsBase):
        HOST: str
        PORT: int
        DB: int
        MAX_CONNECTIONS: int = 10
        DECODE_RESPONSES: bool = True

        @property
        def URL(self) -> str:
            return f"redis://{self.HOST}:{self.PORT}/{self.DB}"

    redis: Redis

    class EventRecord(SettingsBase):
        EventFetchInterval: float = 0.1

    event_record: EventRecord

    @classmethod
    @functools.lru_cache(maxsize=1)
    def from_file(cls, filename: str) -> ty.Self:
        fileutil = FileUtil.from_cwd()
        return cls(**fileutil.read_file(filename))

    def get_modulename(self, filename: str) -> str:
        """
        >>> get_modulename(/src/domain/config.py) -> src.domain.config
        """
        file_path = pathlib.Path(filename).relative_to(self.PROJECT_ROOT)
        return str(file_path).replace("/", ".")[:-3]


@functools.lru_cache(maxsize=1)
def get_setting(filename: str = "settings.toml") -> Settings:
    """
    offcial factory of settings with default filename
    """
    return Settings.from_file(filename=filename)
