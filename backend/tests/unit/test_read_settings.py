import os

from askgpt.domain.config import Settings, detect_settings


def test_read_settings(settings: Settings):
    key = "redis__HOST"
    os.environ[key] = "redis"
    settings = detect_settings()
    assert settings.redis.HOST == "redis"
    del os.environ[key]
