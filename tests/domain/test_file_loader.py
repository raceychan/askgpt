import pathlib

import pytest

from src.domain.fileutil import FileLoader


def test_load_env(fileloader):
    env_file = pathlib.Path("src/.env")
    values = fileloader.handle(env_file)
    assert isinstance(values, dict)


def test_not_file_not_found_err(fileloader):
    error_file = pathlib.Path("none_exists.err")
    with pytest.raises(FileNotFoundError):
        values = fileloader.handle(error_file)


def test_load_toml(fileloader: FileLoader):
    file = pathlib.Path("src/settings.toml")
    values = fileloader.handle(file)
