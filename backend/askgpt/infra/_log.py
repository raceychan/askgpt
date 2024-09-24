from __future__ import annotations  # annotations become strings at runtime

import datetime
import sys
import traceback
import typing as ty

import loguru
import orjson
from loguru import logger
from rich.console import Console

from askgpt.helpers.file import relative_path

__all__ = ["logger"]


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


def format_record(record: loguru.Record) -> dict[str, ty.Any]:
    record_time_utc = record["time"].astimezone(datetime.UTC)
    file_path = relative_path(record["file"].path)
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
      "utmestamp": record_time_utc.timestamp(),
        "exception": traceback.format_exc() if record["exception"] else None,
    } | record["extra"]
    return custom_record


def prod_sink(msg: loguru.Message) -> None:
    string = orjson.dumps(format_record(msg.record)).decode()
    sys.stdout.write(string)
    sys.stdout.flush()


def debug_sink(msg: loguru.Message) -> None:
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
        console.print_exception(show_locals=True)


def update_sink(sink: ty.Callable[[loguru.Message], None]) -> loguru.Logger:
    logger.remove()
    logger.add(sink, level="INFO")
    return logger


update_sink(debug_sink)
