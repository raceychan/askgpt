import pathlib
import typing as ty

from pydantic import BaseModel, ConfigDict

from .fileutil import FileUtil
from .interface import EventLogRef, JournalRef, SystemRef

# from dataclasses import dataclass
# frozen = dataclass(frozen=True, slots=True, kw_only=True, repr=False)


class SettingsBase(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        use_enum_values=True,
        validate_default=True,
        strict=False,
        extra="forbid",
    )


class Settings(SettingsBase):
    PROJECT_NAME: str = "askgpt"
    OPENAI_API_KEY: str

    class DB(SettingsBase):
        DB_DRIVER: str
        ASYNC_DB_DRIVER: str = "aiosqlite"
        DATABASE: pathlib.Path

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

    @classmethod
    def from_file(cls, filename: str = "settings.toml") -> ty.Self:
        fileutil = FileUtil.from_cwd()
        return cls(**fileutil.read_file(filename))
