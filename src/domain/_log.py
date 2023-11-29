from __future__ import annotations  # annotations become strings at runtime

import datetime
import sys
import traceback

import loguru
from loguru import logger as logger_

from src.domain.config import Settings, get_setting

__all__ = ["logger"]


def log_sink(settings: Settings):
    if settings.is_prod_env:
        return prod_sink
    else:
        return sys.stdout


def prod_sink(msg: loguru.Message):
    record = msg.record
    record_time_utc = record["time"].astimezone(datetime.UTC)
    file_path = get_setting().get_modulename(record["file"].path)
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


logger_.remove(0)
logger_.add(
    log_sink(get_setting()),
    level="TRACE",
)

logger = logger_
