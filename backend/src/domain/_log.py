from __future__ import annotations  # annotations become strings at runtime

import datetime
import json
import traceback
import typing as ty

import loguru
from loguru import logger as logger_
from src.domain.config import Settings, get_setting

__all__ = ["logger"]

from rich.console import Console

console = Console(color_system="truecolor")

COLOR_MAPPER = dict(
    TRACE="cyan",
    DEBUG="blue",
    INFO="white",
    SUCCESS="green",
    WARNING="yellow",
    ERROR="red",
    CRITICAL="red",
)
# loguru_fmt = "<green>{time}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | request_id:{request_id} | <level>{message}</level>"


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
    print(json.dumps(custom_record))


def debug_sink(msg: loguru.Message):
    record = msg.record
    record_time_utc = (
        record["time"].astimezone(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S")
    )

    tmplt = "[green]{time}[/] | [level]{level: <8}[/] | [cyan]{name}[/]:[cyan]{function}[/]:[cyan]{line}[/] | [level]{message}[/]"

    if extra := record["extra"]:
        extra_log = " | " + " | ".join(f"{k}={v}" for k, v in extra.items())
    else:
        extra_log = ""

    log = (
        tmplt.format(
            time=record_time_utc,
            level=record["level"],
            name=record["name"],
            function=record["function"],
            line=record["line"],
            message=record["message"],
        )
        + extra_log
    )

    console.print(log, style=COLOR_MAPPER[record["level"].name])
    if record["exception"] and record["level"].name == "debug":
        # trace_text = traceback.format_exc()
        # console.print(trace_text, style="red")
        console.print_exception(show_locals=True)


def config_logs(settings: Settings):
    logger_.remove(0)
    if settings.is_prod_env:
        logger_.add(prod_sink, level="INFO")
    else:
        logger_.add(debug_sink, level="INFO")
    return logger_


logger = config_logs(get_setting())
