import pathlib

import pytest

from src.domain.fileutil import FileLoader  # , value_parser


def test_load_env(fileloader: FileLoader, tmp_path: pathlib.Path):
    env_file = tmp_path / ".env"
    env_file.write_text("TEST=true")
    values = fileloader.handle(env_file)
    assert values["TEST"] == "true"
    assert isinstance(values, dict)


def test_not_file_not_found_err(fileloader: FileLoader):
    error_file = pathlib.Path("none_exists.err")
    with pytest.raises(FileNotFoundError):
        _ = fileloader.handle(error_file)


def test_load_toml(fileloader: FileLoader, tmp_path: pathlib.Path):
    toml = tmp_path / "settings.toml"
    toml.write_text("TEST=true")
    file = pathlib.Path(toml)
    values = fileloader.handle(file)
    assert values["TEST"] is True
