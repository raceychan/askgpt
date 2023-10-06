from src.domain.fileutil import FileUtil


def test_read_config(fileutil: FileUtil):
    values = fileutil.read_file("src/settings.toml")
