# type: ignore
import asyncio
import inspect
import signal
import types
import typing as ty
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from time import perf_counter

from askgpt.domain._log import logger
from askgpt.helpers.extratypes import AnyCallable



@dataclass(frozen=True, kw_only=True, slots=True, repr=False, unsafe_hash=True)
class FuncInfo:
    name: str
    code: str
    signature: inspect.Signature
    location: str
    is_async: bool

    def __repr__(self):
        return f"<FuncInfo {self.location} {self.name}{str(self.signature)}>"

    def __str__(self):
        return f"{self.location} {self.name}"

    @classmethod
    def from_func(cls, func: AnyCallable):
        name = func.__qualname__
        func_code = func.__code__
        code = inspect.getsource(func)
        sig = inspect.signature(func)
        is_async = inspect.iscoroutinefunction(func)
        location = f"{func_code.co_filename}({func_code.co_firstlineno})"

        funcinfo = cls(
            name=name,
            code=code,
            signature=sig,
            location=location,
            is_async=is_async,
        )
        return funcinfo


@dataclass(frozen=True, kw_only=True, slots=True, unsafe_hash=True)
class ExecInfo:
    funcinfo: FuncInfo
    args: tuple[ty.Any, ...]
    kwargs: dict[str, ty.Any]
    timecost: float
    unit: ty.Literal["ns", "ms", "s"] = "s"

    def format_repr(self, with_args: bool = False):
        if with_args:
            raise NotImplementedError
        fmt = f"{self.funcinfo.location} {self.funcinfo.name} {self.timecost:.3f}{self.unit}"
        return fmt

    def __repr__(self) -> str:
        fmt = f"<ExecInfo {str(self.funcinfo)} {self.timecost:.3f}{self.unit}>"
        return fmt

    def __str__(self) -> str:
        return self.format_repr()


@ty.overload
def timeit[R, **P](func: ty.Callable[P, R]) -> ty.Callable[P, R]: ...


@ty.overload
def timeit[
    R, **P
](func: ty.Callable[P, ty.Awaitable[R]]) -> ty.Callable[P, ty.Awaitable[R]]: ...


def timeit[
    R, **P
](
    _func: AnyCallable | None = None,
    *,
    unit: ty.Literal["ns", "ms", "s"] = "ms",
    precision: int = 2,
    log_if: ty.Callable[[float], bool] = lambda x: x > 0.1,
    with_args: bool = False,
):
    log_tmplt = "Executed {function_name} in {time_cost}{unit}"

    def decorator(func: ty.Callable[P, R]) -> ty.Callable[P, R]:
        funcinfo = FuncInfo.from_func(func)

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs):
            start = perf_counter()
            res = func(*args, **kwargs)
            end = perf_counter()
            timecost = round(end - start, precision)

            if log_if(timecost):
                log_msg = log_tmplt.format(
                    function_name=funcinfo.name, time_cost=timecost, unit=unit
                )
                logger.info(log_msg)
            return res

        @wraps(func)
        async def awrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start = perf_counter()
            res = await func(*args, **kwargs)
            end = perf_counter()
            timecost = round(end - start, precision)

            if log_if(timecost):
                log_msg = log_tmplt.format(
                    function_name=funcinfo.name, time_cost=timecost, unit=unit
                )
                logger.info(log_msg)
            return res

        return awrapper if inspect.iscoroutinefunction(func) else wrapper  # type: ignore

    if _func is None:
        return decorator
    else:
        return decorator(_func)


class TimeoutException(Exception):
    pass


class Timeout:
    def __init__(self, seconds: int, error_msg: str = ""):
        self.seconds = seconds
        self.error_msg = error_msg or f"Timed out after {seconds} seconds"

    def handle_timeout(self, signume: int, frame: ty.Any):
        raise TimeoutException(self.error_msg)

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)

    def __exit__(
        self,
        exc_type: ty.Type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ):
        signal.alarm(0)


def timeout(seconds: int):
    def decor_dispatch(func):
        def sync_timeout(*args, **kwargs):
            raise NotImplementedError

        async def async_timeout(*args, **kwargs):
            coro = func(*args, **kwargs)
            res = await asyncio.wait_for(coro, seconds)
            return res

        return async_timeout

    return decor_dispatch

