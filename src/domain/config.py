import pathlib
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict

from src.domain.fileutil import FileUtil

frozen = dataclass(frozen=True, slots=True, kw_only=True, repr=False)


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

    @classmethod
    def from_file(cls, filename: str = "settings.toml"):
        fileutil = FileUtil.from_cwd()
        return cls(**fileutil.read_file(filename))



# settings = Settings.from_file("settings.toml")
