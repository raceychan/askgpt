import pathlib
import typing as ty

from pydantic import BaseModel, ConfigDict, computed_field, field_validator
from src.domain.base import KeySpace, TimeScale, freeze, freezelru
from src.domain.interface import SQL_ISOLATIONLEVEL, EventLogRef, JournalRef, SystemRef
from src.toolkit.fileutil import FileUtil

UNIT = MINUTE = 1
HOUR = 60 * MINUTE
DAY = 24 * HOUR
WEEK = 7 * DAY


TIME_EPSILON_S = 0.001  # 1ms


class UnknownAddress(ty.NamedTuple):
    ip: str = "unknown_ip"
    port: str = "unknown_port"


class SettingsFactory[T](ty.Protocol):
    def __call__(self, settings: "Settings") -> T:  # | ty.AsyncGenerator[T, None]:
        ...


class PureFacotry[T](ty.Protocol):
    def __call__(self) -> T:
        ...


def settingfactory[T: ty.Any](factory: SettingsFactory[T]) -> SettingsFactory[T]:
    "Cached factory that returns a cached instance for each settings instance"
    return freezelru(factory)


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
    RUNTIME_ENV: ty.Literal["dev", "prod", "test"]

    @property
    def is_prod_env(self):
        return self.RUNTIME_ENV == "prod"

    class DB(SettingsBase):
        DIALECT: str
        DRIVER: str

        USER: str
        PASSWORD: str
        HOST: str
        PORT: int

        @property
        def DB_URL(self) -> str:
            proto = f"{self.DIALECT}+{self.DRIVER}" if self.DRIVER else self.DIALECT
            base = f"{proto}://"
            if self.USER and self.PASSWORD:
                base += f"{self.USER}:{self.PASSWORD}"
            elif self.USER:
                base += self.USER
            elif self.PASSWORD:
                raise ValueError("Password without user is not allowed")

            if self.HOST:
                base += f"@{self.HOST}"
            if self.PORT != -1:
                base += f":{self.PORT}"
            if self.DATABASE:
                base += f"/{self.DATABASE}"
            return base

        DATABASE: pathlib.Path
        ISOLATION_LEVEL: SQL_ISOLATIONLEVEL
        ENGINE_ECHO: bool = False

        class CONNECT_ARGS(SettingsBase):
            """
            Driver-specific connection arguments
            https://magicstack.github.io/asyncpg/current/api/index.html
            """

            server_settings: dict[str, ty.Any] | None = None

        connect_args: dict  # CONNECT_ARGS

        class ExeuctionOptions(SettingsBase):
            "Sqlalchemy engine-specific options"
            ...

        execution_options: ExeuctionOptions

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
        SCHEME: ty.Literal["redis", "rediss", "unix"] = "redis"
        HOST: str
        PORT: int | str
        DB: int | str
        TOKEN_BUCKET_SCRIPT: pathlib.Path = pathlib.Path("src/script/tokenbucket.lua")
        MAX_CONNECTIONS: int = 10
        DECODE_RESPONSES: bool = True
        SOCKET_TIMEOUT: int
        SOCKET_CONNECT_TIMEOUT: int = 2

        # KEY_SPACE: KeySpace

        @property
        def URL(self) -> str:
            return f"{self.SCHEME}://{self.HOST}:{self.PORT}/{self.DB}"

        class KeySpaces(SettingsBase):
            APP: KeySpace

            @field_validator("APP", "THROTTLER", mode="before")
            @classmethod
            def validate_key_space(cls, v: str) -> KeySpace:
                return KeySpace(v)

            @computed_field
            @property
            def THROTTLER(cls) -> KeySpace:
                return cls.APP("throttler")

            @computed_field
            @property
            def API_POOL(cls) -> KeySpace:
                return cls.APP("apikeypool")

        keyspaces: KeySpaces

    redis: Redis

    class Throttling(SettingsBase):
        USER_MAX_REQUEST_PER_MINUTE: int
        USER_MAX_REQUEST_DURATION_MINUTE: int

    throttling: Throttling

    class EventRecord(SettingsBase):
        EventFetchInterval: float = 0.1

    event_record: EventRecord

    @classmethod
    @freezelru
    def from_file(cls, filename: str) -> ty.Self:
        fileutil = FileUtil.from_cwd()
        config_data = fileutil.read_file(filename)
        return cls.model_validate(config_data)

    def get_modulename(self, filename: str) -> str:
        """
        >>> get_modulename(/src/domain/config.py) -> src.domain.config
        """
        file_path = pathlib.Path(filename).relative_to(self.PROJECT_ROOT)
        return str(file_path).replace("/", ".")[:-3]


@freezelru
def get_setting(filename: str = "settings.toml") -> Settings:
    """
    offcial factory of settings with default filename
    """
    settings = Settings.from_file(filename=filename)
    return settings
