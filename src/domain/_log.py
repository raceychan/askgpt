from __future__ import annotations

import datetime
import sys
import traceback
from pathlib import Path

import loguru
from loguru import logger as _logger

from src.domain.config import Settings, settings

__all__ = ["logger"]


def log_sink(settings: Settings):
    if settings.is_prod_env:
        return prod_sink
    else:
        return sys.stdout


def prod_sink(msg: loguru.Message):
    record = msg.record
    record_time_utc = record["time"].astimezone(datetime.UTC)

    project_root = settings().PROJECT_ROOT
    file_path = Path(record["file"].path).relative_to(project_root)

    custom_record = {
        "level": record["level"].name,
        "msg": record["message"],
        "file": file_path,
        "line": record["line"],
        "process_name": record["process"].name,
        "process_id": record["process"].id,
        "thread_name": record["thread"].name,
        "thread_id": record["thread"].id,
        "utcdatetime": record_time_utc.strftime("%Y-%m-%d %H:%M:%S"),
        "utctimestamp": record_time_utc.timestamp(),
        "exception": traceback.format_exc() if record["exception"] else None,
    } | record["extra"]

    print(custom_record)


_logger.remove(0)
_logger.add(
    log_sink(settings()),
    level="TRACE",
)

logger = _logger
