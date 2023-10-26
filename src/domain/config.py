from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict
from src.domain.fileutil import FileUtil

frozen = dataclass(frozen=True, slots=True, kw_only=True, repr=False)


class SettingsBase(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        use_enum_values=True,
        validate_default=True,
        strict=True,
        extra="forbid",
    )


class Settings(SettingsBase):
    PROJECT_NAME: str = "askgpt"
    OPENAI_API_KEY: str

    class DB(SettingsBase):
        DB_DRIVER: str
        ASYNC_DB_DRIVER: str = "aiosqlite"
        DATABASE: str

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


class TestDefaults:
    user_id: str = "admin"
    session_id: str = "default_session"
    model: str = "gpt-3.5-turbo"


# settings = Settings.from_file("settings.toml")
