import datetime
import os
import pathlib
import typing as ty
from contextvars import ContextVar

import jose.constants
from pydantic import AnyUrl, BaseModel, ConfigDict
from pydantic import SecretStr as SecretStr
from pydantic import field_validator

from askgpt.domain.errors import StaticAPPError
from askgpt.domain.interface import SQL_ISOLATIONLEVEL, EventLogRef, SystemRef
from askgpt.helpers.data import update_config_from_env
from askgpt.helpers.file import FileUtil
from askgpt.helpers.functions import freeze, simplecache
from askgpt.helpers.string import KeySpace

UNIT = MINUTE = 1
HOUR = 60 * MINUTE
DAY = 24 * HOUR
WEEK = 7 * DAY


TIME_EPSILON_S = 0.001  # 1ms


type SUPPORTED_ALGORITHMS = ty.Literal[tuple(jose.constants.ALGORITHMS.SUPPORTED)]  # type: ignore

SETTINGS_READ_ORDER: tuple[str, ...] = (
    "test.settings.toml",
    "dev.settings.toml",
    "prod.settings.toml",
    "settings.toml",
    "test.env",
    "dev.env",
    "prod.env",
    ".env",
)

UNKNOWN_NETLOC = ("unknown_ip", "unknown_port")

UTC_TZ = datetime.UTC


def detect_settings(read_order: tuple[str, ...] = SETTINGS_READ_ORDER) -> "Settings":
    fileutil = FileUtil.from_cwd()
    work_dir = pathlib.Path.cwd()
    if (f := os.environ.get("SETTING_FILE", None)) is not None:
        return Settings.from_file(fileutil.find(f))
    for candidate in read_order:
        try:
            f = fileutil.find(candidate, dir=work_dir)
        except FileNotFoundError:
            continue
        else:
            settings = Settings.from_file(f)
            return settings
    raise FileNotFoundError(f"None of {read_order} File exists in {work_dir}")


def sys_finetune():
    import gc
    import sys

    # set max times of recursion to 10000
    sys.setrecursionlimit(10000)

    # drop gil every 1 second, remove this after python 3.14
    sys.setswitchinterval(1)

    # zero_gen gc gets revoked when live objects reach 3000(allocated - deallocated)
    gc.set_threshold(3000, 100, 100)


class SettingsFactory[T](ty.Protocol):
    def __call__(self, settings: "Settings") -> T: ...


class PureFacotry[T](ty.Protocol):
    def __call__(self) -> T: ...


def settingfactory[T: ty.Any](factory: SettingsFactory[T]) -> SettingsFactory[T]:
    "Cached factory that returns a cached instance for each settings instance"
    return simplecache(max_size=1, size_check=True)(factory)  # type: ignore


class MissingConfigError(StaticAPPError):
    """
    Essential config is missing for some components.
    """

    def __int__(self, config_type: type["SettingsBase"]):
        msg = f"setting {config_type} is missing"
        super().__init__(msg)


class SettingsBase(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        use_enum_values=True,
        validate_default=True,
        strict=False,
        extra="forbid",
    )

    def __hash__(self) -> int:
        vals = tuple(freeze(v) for v in self.__dict__.values())
        return hash(self.__class__) + hash(vals)


class Settings(SettingsBase):
    PROJECT_NAME: ty.ClassVar[str] = "askgpt"
    PROJECT_ROOT: ty.ClassVar[pathlib.Path] = pathlib.Path.cwd()
    FILE_NAME: str | None = None
    RUNTIME_ENV: ty.Literal["dev", "prod", "test"]

    @property
    def is_prod_env(self):
        return self.RUNTIME_ENV == "prod"

    class Security(SettingsBase):
        SECRET_KEY: SecretStr  # 32 bytes url safe string
        ALGORITHM: SUPPORTED_ALGORITHMS  # jose.constants.ALGORITHMS
        ACCESS_TOKEN_EXPIRE_MINUTES: int
        CORS_ORIGINS: list[str]

        @field_validator("CORS_ORIGINS", mode="before")
        def _(cls, v: str) -> list[str]:
            if isinstance(v, list):
                return v
            return v.split(",")

    security: Security

    class DB(SettingsBase):
        """
        Perhaps separate this for PGDB, SqliteDB, MysqlDB etc.
        """

        DIALECT: str
        DRIVER: str

        USER: str
        PASSWORD: SecretStr
        HOST: str = ""
        PORT: int = -1
        DATABASE: pathlib.Path | ty.Literal[":memory:"]

        ISOLATION_LEVEL: SQL_ISOLATIONLEVEL
        ENGINE_ECHO: bool = False

        @property
        def DB_URL(self) -> str:
            proto = f"{self.DIALECT}+{self.DRIVER}" if self.DRIVER else self.DIALECT
            url = f"{proto}://"
            if self.USER and self.PASSWORD:
                url += f"{self.USER}:{self.PASSWORD}"
            elif self.USER:
                url += self.USER
            elif self.PASSWORD:
                raise ValueError("Password without user is not allowed")

            if self.HOST:  # host can be None if we use sqlite
                url += f"@{self.HOST}"
            if self.PORT != -1:
                url += f":{self.PORT}"
            if self.DATABASE:
                url += f"/{self.DATABASE}"
            return url

        class CONNECT_ARGS(SettingsBase):
            """
            Driver-specific connection arguments
            https://magicstack.github.io/asyncpg/current/api/index.html
            """

            server_settings: dict[str, ty.Any] | None = None

        connect_args: CONNECT_ARGS | None = None

        class ExeuctionOptions(SettingsBase):
            "Sqlalchemy engine-specific options"
            ...

        execution_options: ExeuctionOptions | None = None

    class SqliteDB(DB):
        DIALECT: str = "sqlite"
        DRIVER: str = "aiosqlite"
        HOST: str = ""
        PORT: int = -1
        USER: str = ""
        PASSWORD: SecretStr = SecretStr("")

        DATABASE: pathlib.Path | ty.Literal[":memory:"]
        ISOLATION_LEVEL: SQL_ISOLATIONLEVEL = "SERIALIZABLE"

    class Postgres(DB):
        DIALECT: str = "postgres"
        DRIVER: str = "aiopg"

    db: DB

    class ActorRefs(SettingsBase):
        SYSTEM: SystemRef = SystemRef("system")  # type: ignore
        EVENTLOG: EventLogRef = EventLogRef("eventlog")  # type: ignore

    actor_refs: ActorRefs

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
        SCHEME: ty.Literal["redis", "rediss", "unix"] = "redis"
        HOST: str
        PORT: int | str
        PASSWORD: SecretStr | None = None
        DB: int | str
        TOKEN_BUCKET_SCRIPT: pathlib.Path = pathlib.Path(
            "askgpt/script/tokenbucket.lua"
        )
        MAX_CONNECTIONS: int = 10
        DECODE_RESPONSES: bool = True
        SOCKET_TIMEOUT: int = 10
        SOCKET_CONNECT_TIMEOUT: int = 2

        @property
        def URL(self) -> str:
            url = AnyUrl.build(
                scheme=self.SCHEME,
                host=self.HOST,
                port=int(self.PORT),
                password=str(self.PASSWORD) if self.PASSWORD else None,
                path=str(self.DB),
            )
            return str(url)

        class KeySpaces(SettingsBase):
            APP: KeySpace

            @field_validator("APP", mode="before")
            @classmethod
            def validate_key_space(cls, v: str) -> KeySpace:
                return KeySpace(v)

            @property
            def THROTTLER(cls) -> KeySpace:
                return cls.APP / "throttler"

            @property
            def API_POOL(cls) -> KeySpace:
                return cls.APP / "apikeypool"

        keyspaces: KeySpaces

    redis: Redis

    class Throttling(SettingsBase):
        USER_MAX_REQUEST_PER_MINUTE: int
        USER_MAX_REQUEST_DURATION_MINUTE: int

    throttling: Throttling

    class EventRecord(SettingsBase):
        EVENT_FETCH_INTERVAL: float = 0.1

    event_record: EventRecord

    class OpenAIClient(SettingsBase):
        TIMEOUT: float = 30.0
        MAX_RETRIES: int = 3

    openai_client: OpenAIClient

    @classmethod
    @simplecache
    def from_file(cls, filename: str | pathlib.Path) -> ty.Self:
        fileutil = FileUtil.from_cwd()
        config_data = fileutil.read_file(filename)
        config_data["FILE_NAME"] = str(filename)
        updated_config = update_config_from_env(config_data)
        return cls.model_validate(updated_config)


SETTINGS_CONTEXT: ContextVar[Settings] = ContextVar("settings")
