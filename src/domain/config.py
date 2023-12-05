import functools
import pathlib
import secrets
import typing as ty

from pydantic import BaseModel, ConfigDict

from src.domain.fileutil import FileUtil
from src.domain.interface import SQL_ISOLATIONLEVEL, EventLogRef, JournalRef, SystemRef


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
    OPENAI_API_KEY: str
    RUNTIME_ENV: ty.Literal["dev", "prod", "test"]

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
        SECRET_KEY: str
        ALGORITHM: str = "HS256"
        # expire in 7 days
        ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    security: Security

    class API(SettingsBase):
        API_VERSION: str = "1"
        API_VERSION_STR: str = f"/v{API_VERSION}"
        OPEN_API: str = f"{API_VERSION_STR}/openapi.json"
        DOCS: str = f"{API_VERSION_STR}/docs"
        REDOC: str = f"{API_VERSION_STR}/redoc"
        SECRET_KEY: str = secrets.token_urlsafe(32)
        ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8

    api: API

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


def get_setting(filename: str = "settings.toml") -> Settings:
    """
    offcial factory of settings, same as Settings.from_file()
    """
    return Settings.from_file(filename=filename)
