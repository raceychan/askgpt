from __future__ import annotations  # annotations become strings at runtime

import datetime
import traceback
import typing as ty

import loguru
from loguru import logger as logger_

from src.domain.config import Settings, get_setting
from src.domain.fmtutils import fprint

__all__ = ["logger"]

from rich.console import Console

console = Console(color_system="truecolor")


def format_record(record: loguru.Record) -> dict[str, ty.Any]:
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
    return custom_record


def prod_sink(msg: loguru.Message):
    record = msg.record
    custom_record = format_record(record)
    fprint(str(custom_record))


def debug_sink(msg: loguru.Message):
    record = msg.record
    record_time_utc = (
        record["time"].astimezone(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S")
    )
    fmt = "[green]{time}[/green] | [level]{level: <8}[/level] | [cyan]{name}[/cyan]:[cyan]{function}[/cyan]:[cyan]{line}[/cyan] - {request_id} - [level]{message}[/level]"

    log = fmt.format(
        time=record_time_utc,
        level=record["level"],
        name=record["name"],
        function=record["function"],
        line=record["line"],
        message=record["message"],
        request_id=record["extra"].get("request_id", ""),
    )
    console.print(log)


def config_logs(settings: Settings):
    logger_.remove(0)
    if settings.is_prod_env:
        logger_.add(prod_sink, level="INFO")
    else:
        logger_.add(debug_sink, level="INFO")
        # logger_.configure(
        #     handlers=[
        #         dict(
        #             sink=sys.stdout,
        #             level="TRACE",
        #         )
        #     ],
        # )

    return logger_


logger = config_logs(get_setting())
