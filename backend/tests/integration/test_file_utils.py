import pathlib

from src.helpers.file import FileUtil


def test_read_config(fileutil: FileUtil, tmp_path: pathlib.Path):
    # TODO: test yaml and .env
    toml = tmp_path / "test_settings.toml"
    toml.write_text("TEST=true")
    file = pathlib.Path(toml)
    values = fileutil.read_file(file)
    assert values["TEST"] is True
