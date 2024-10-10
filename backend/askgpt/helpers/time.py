import asyncio
import datetime
import inspect
import signal
import types
import typing as ty
from dataclasses import dataclass
from functools import wraps
from time import perf_counter

from askgpt.helpers.extratypes import AnyCallable

if ty.TYPE_CHECKING:
    from loguru import Logger


def utc_now(timestamp: float | None = None) -> datetime.datetime:
    """
    UTC datetime
    """

    if timestamp is not None:
        now_ = datetime.datetime.fromtimestamp(timestamp)
    else:
        now_ = datetime.datetime.now(datetime.UTC)

    return now_


def iso_now() -> str:
    """
    UTC datetime in iso format:
    "YYYY-MM-DD HH:MM:SS.mmmmmm"
    """
    return utc_now().isoformat()


@dataclass(frozen=True, kw_only=True, slots=True, repr=False, unsafe_hash=True)
class FuncInfo:
    name: str
    code: str
    signature: inspect.Signature
    location: str
    is_async: bool

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.location} {self.name}{str(self.signature)}>"

    def __str__(self):
        return f"{self.location} {self.name}"

    @classmethod
    def from_func(cls, func: AnyCallable) -> ty.Self:
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
def timeit[
    R, **P
](_func: ty.Callable[P, R]) -> ty.Callable[P, R]:  # Sync function, no kwargs
    ...


@ty.overload
def timeit[
    R, **P
](_func: ty.Callable[P, ty.Awaitable[R]]) -> ty.Callable[
    P, ty.Awaitable[R]
]:  # Async function, no kwargs
    ...


@ty.overload
def timeit[
    R, **P
](
    _func: None = None,
    *,
    logger: ty.Optional["Logger"] = None,
    unit: ty.Literal["ns", "ms", "s"] = "ms",
    precision: int = 2,
    log_threadhold: ty.Callable[[float], bool] = lambda x: x > 0.1,
    with_args: bool = False,
) -> ty.Callable[
    [ty.Callable[P, R]], ty.Callable[P, R]
]:  # Sync function with kwargs
    ...


@ty.overload
def timeit[
    R, **P
](
    _func: None = None,
    *,
    logger: ty.Optional["Logger"] = None,
    unit: ty.Literal["ns", "ms", "s"] = "ms",
    precision: int = 2,
    log_threadhold: ty.Callable[[float], bool] = lambda x: x > 0.1,
    with_args: bool = False,
) -> ty.Callable[
    [ty.Callable[P, ty.Awaitable[R]]], ty.Callable[P, ty.Awaitable[R]]
]: ...


def timeit[
    R, **P
](
    _func: ty.Callable[P, R] | None = None,
    *,
    logger: ty.Optional["Logger"] = None,
    unit: ty.Literal["ns", "ms", "s"] = "ms",
    precision: int = 2,
    log_threadhold: ty.Callable[[float], bool] = lambda x: x > 0.1,
    with_args: bool = False,
):

    @ty.overload
    def decorator(func: ty.Callable[P, ty.Awaitable[R]]) -> ty.Callable[P, R]: ...

    @ty.overload
    def decorator(func: ty.Callable[P, R]) -> ty.Callable[P, R]: ...

    def decorator(
        func: ty.Callable[P, R] | ty.Callable[P, ty.Awaitable[R]]
    ) -> ty.Callable[P, R] | ty.Callable[P, ty.Awaitable[R]]:
        def build_logmsg(
            pre: float,
            aft: float,
        ):
            timecost = round(pre - aft, precision)
            if unit == "ms":
                timecost *= 10**3
            elif unit == "ns":
                timecost *= 10**6

            msg = f"Executed {func} in {timecost}{unit}"
            return msg

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start = perf_counter()
            f = ty.cast(ty.Callable[P, R], func)
            res = f(*args, **kwargs)
            end = perf_counter()
            timecost = round(end - start, precision)

            if not log_threadhold(timecost):
                return res

            if logger:
                logger.info(build_logmsg(start, end))
            return res

        @wraps(func)
        async def awrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start = perf_counter()
            f = ty.cast(ty.Callable[P, ty.Awaitable[R]], func)
            res = await f(*args, **kwargs)
            end = perf_counter()
            timecost = round(end - start, precision)
            if not log_threadhold(timecost):
                return res
            if logger:
                logger.info(build_logmsg(start, end))

            return res

        if inspect.iscoroutinefunction(func):
            return awrapper
        return wrapper

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


def timeout(seconds: int, *, logger: ty.Optional["Logger"] = None):
    def decor_dispatch(func):
        def sync_timeout(*args, **kwargs):
            raise NotImplementedError

        async def async_timeout(*args, **kwargs):
            coro = func(*args, **kwargs)
            try:
                res = await asyncio.wait_for(coro, seconds)
            except TimeoutError as te:
                if logger:
                    logger.exception(f"{func} timesout after {seconds}s")
            return res

        return async_timeout

    return decor_dispatch
