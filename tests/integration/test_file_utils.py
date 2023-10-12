import pathlib

from src.domain.fileutil import FileUtil


def test_read_config(fileutil: FileUtil, tmp_path: pathlib.Path):
    toml = tmp_path / "settings.toml"
    toml.write_text("TEST=true")
    file = pathlib.Path(toml)
    values = fileutil.read_file(file)
    assert values["TEST"] == True
