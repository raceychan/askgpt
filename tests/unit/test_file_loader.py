import pathlib

import pytest

from src.domain.fileutil import FileLoader, value_parser


def test_value_parser():
    assert value_parser("3.5") == 3.5
    assert value_parser("3") == 3
    assert value_parser("0.0.1") == "0.0.1"
    assert value_parser("'name'") == "name"
    inproperly_quoted_str = """
            'a"
    """.strip()
    with pytest.raises(ValueError):
        value_parser(inproperly_quoted_str)


def test_load_env(fileloader, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("TEST=true")
    values = fileloader.handle(env_file)
    assert values["TEST"] is True
    assert isinstance(values, dict)


def test_not_file_not_found_err(fileloader):
    error_file = pathlib.Path("none_exists.err")
    with pytest.raises(FileNotFoundError):
        _ = fileloader.handle(error_file)


def test_load_toml(fileloader: FileLoader, tmp_path):
    toml = tmp_path / "settings.toml"
    toml.write_text("TEST=true")
    file = pathlib.Path(toml)
    values = fileloader.handle(file)
    assert values["TEST"] is True
