import typing
from dataclasses import dataclass


def read_env(filename: str = ".env") -> dict[str, typing.Any]:
    from pathlib import Path

    file = Path(__file__).parent / filename
    if not file.exists():
        raise Exception(f"{filename} file not found")

    def parse(val: str):
        if val[0] in {'"', "'"}:  # Removing quotes if they exist
            if val[0] == val[-1]:
                value = val[1:-1]
            else:
                raise ValueError(f"{val} inproperly quoted")

        # Type casting
        if val.isdecimal():
            value = int(val)  # Integer type
        elif val.lower() in {"true", "false"}:
            value = val.lower() == "true"  # Boolean type
        else:
            if val[0].isdecimal():  # Float type
                try:
                    value = float(val)
                except ValueError as ve:
                    pass
                else:
                    return value
            value = val  # Otherwise, string type
        return value

    config = {}
    ln = 1

    with file.open() as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                try:
                    key, value = line.split("=", 1)
                    config[key.strip()] = parse(value.strip())
                except ValueError as ve:
                    raise Exception(f"Invalid env line number {ln}: {line}") from ve
            ln += 1
    return config


@dataclass(frozen=True, slots=True, kw_only=True)
class Config:
    OPENAI_API_KEY: str
    DB_DRIVER: str = "sqlite"
    DATABASE: str = "./eventstore.db"

    DB_URL: str = f"{DB_DRIVER}:///{DATABASE}"
    ASYNC_DB_URL: str = f"{DB_DRIVER}+aiosqlite:///{DATABASE}"

    @classmethod
    def from_env(cls, file_name: str = ".env") -> "Config":
        env = read_env(file_name)
        return cls(**env)
