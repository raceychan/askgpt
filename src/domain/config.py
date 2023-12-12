import functools
import pathlib
import secrets
import typing as ty

from pydantic import BaseModel, ConfigDict

from src.domain.fileutil import FileUtil
from src.domain.interface import SQL_ISOLATIONLEVEL, EventLogRef, JournalRef, SystemRef


class TimeScale:
    "A more type-aware approach to time scale"
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
    # default values are for testing
    PROJECT_NAME: ty.ClassVar[str] = "askgpt"
    PROJECT_ROOT: ty.ClassVar[pathlib.Path] = pathlib.Path.cwd()
    OPENAI_API_KEY: str
    RUNTIME_ENV: ty.Literal["dev", "prod", "test"]

    # make pyright happy, Settings is hashable by setting frozen=True
    __hash__: ty.Callable[[None], int]

    class DB(SettingsBase):
        DB_DRIVER: str = "sqlite"
        ASYNC_DB_DRIVER: str = "aiosqlite"
        DATABASE: pathlib.Path
        ISOLATION_LEVEL: SQL_ISOLATIONLEVEL = "SERIALIZABLE"
        ENGINE_ECHO: bool = False

        @property
        def DB_URL(self) -> str:
            return f"{self.DB_DRIVER}:///{self.DATABASE}"

        @property
        def ASYNC_DB_URL(self) -> str:
            return f"{self.DB_DRIVER}+{self.ASYNC_DB_DRIVER}:///{self.DATABASE}"

    db: DB

    class ActorRefs(SettingsBase):
        SYSTEM: SystemRef = SystemRef("system")
        EVENTLOG: EventLogRef = EventLogRef("eventlog")
        JOURNAL: JournalRef = JournalRef("journal")

    actor_refs: ActorRefs

    class Security(SettingsBase):
        SECRET_KEY: str = secrets.token_urlsafe(32)
        ALGORITHM: str = "HS256"
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

    class Cache(SettingsBase):
        HOST: str = "localhost"
        PORT: int = 6379
        DB: int = 0

    cache: Cache

    @property
    def is_prod_env(self):
        return self.RUNTIME_ENV == "prod"

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
