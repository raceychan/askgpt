import asyncio
import datetime
import inspect
import signal
import types
import typing as ty
from contextlib import contextmanager
from functools import wraps
from time import perf_counter

if ty.TYPE_CHECKING:
    from logging import Logger as StdLogger

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


type SimpleDecor[**P, R] = ty.Callable[P, R]
type ParamDecor[**P, R] = ty.Callable[[ty.Callable[P, R]], ty.Callable[P, R]]
type AsyncSimpleDecor[**P, R] = ty.Callable[P, ty.Awaitable[R]]
type AsyncParamDecor[**P, R] = ty.Callable[
    [ty.Callable[P, ty.Awaitable[R]]], ty.Callable[P, ty.Awaitable[R]]
]
type FlexDecor[**P, R] = SimpleDecor | ParamDecor | AsyncSimpleDecor | AsyncParamDecor


# Sync function, no kwargs
@ty.overload
def timeit[R, **P](func__: ty.Callable[P, R]) -> SimpleDecor[P, R]: ...


# Async function, no kwargs
@ty.overload
def timeit[
    R, **P
](func__: ty.Callable[P, ty.Awaitable[R]]) -> AsyncSimpleDecor[P, R]: ...


# Sync function with kwargs
@ty.overload
def timeit[
    R, **P
](
    *,
    logger: ty.Optional[ty.Union["Logger", "StdLogger"]] = None,
    precision: int = 2,
    log_threshold: float = 0.1,
    with_args: bool = False,
) -> ParamDecor[P, R]: ...


@ty.overload
def timeit[
    R, **P
](
    *,
    logger: ty.Optional[ty.Union["Logger", "StdLogger"]] = None,
    precision: int = 2,
    log_threshold: float = 0.1,
    with_args: bool = False,
) -> AsyncParamDecor[P, R]: ...


@ty.overload
def timeit[
    R, **P
](
    *,
    logger: ty.Optional[ty.Callable[[float], None]] = None,
    precision: int = 2,
    log_threshold: float = 0.1,
) -> ParamDecor[P, R]: ...


@ty.overload
def timeit[
    R, **P
](
    *,
    logger: ty.Optional[ty.Callable[[float], None]] = None,
    precision: int = 2,
    log_threshold: float = 0.1,
) -> AsyncParamDecor[P, R]: ...


def timeit[
    R, **P
](
    func__: ty.Callable[P, R] | None = None,
    *,
    logger: ty.Optional[
        ty.Union["Logger", "StdLogger", ty.Callable[[float], None]]
    ] = None,
    precision: int = 2,
    log_threshold: float = 0.1,
    with_args: bool = False,
    show_fino: bool = True,
) -> FlexDecor:

    @ty.overload
    def decorator(func: ty.Callable[P, ty.Awaitable[R]]) -> ty.Callable[P, R]: ...

    @ty.overload
    def decorator(func: ty.Callable[P, R]) -> ty.Callable[P, R]: ...

    def decorator(
        func: ty.Callable[P, R] | ty.Callable[P, ty.Awaitable[R]]
    ) -> ty.Callable[P, R] | ty.Callable[P, ty.Awaitable[R]]:
        def build_logmsg(
            timecost: float,
            func_args: tuple,
            func_kwargs: dict,
        ):

            func_repr = func.__qualname__
            if with_args:
                arg_repr = ", ".join(f"{arg}" for arg in func_args)
                kwargs_repr = ", ".join(f"{k}={v}" for k, v in func_kwargs.items())
                func_repr = f"{func_repr}({arg_repr}, {kwargs_repr})"

            msg = f"{func_repr} {timecost}s"

            if show_fino:
                func_code = func.__code__
                location = f"{func_code.co_filename}({func_code.co_firstlineno})"
                msg = f"{location} {msg}"

            return msg

        @contextmanager
        def log_callback(args, kwargs):
            pre = perf_counter()
            yield
            aft = perf_counter()
            timecost = round(aft - pre, precision)

            if timecost < log_threshold:
                return

            if logger:
                if callable(logger):
                    logger(timecost)
                else:
                    logger.info(build_logmsg(timecost, args, kwargs))
            else:
                print(build_logmsg(timecost, args, kwargs))

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            f = ty.cast(ty.Callable[P, R], func)
            with log_callback(args, kwargs):
                res = f(*args, **kwargs)
            return res

        @wraps(func)
        async def awrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            f = ty.cast(ty.Callable[P, ty.Awaitable[R]], func)
            with log_callback(args, kwargs):
                res = await f(*args, **kwargs)
            return res

        if inspect.iscoroutinefunction(func):
            return awrapper
        else:
            return wrapper

    if func__ is None:
        return decorator
    else:
        return decorator(func__)


class Timeout:
    def __init__(self, seconds: int, error_msg: str = ""):
        self.seconds = seconds
        self.error_msg = error_msg or f"Timed out after {seconds} seconds"

    def handle_timeout(self, signume: int, frame: ty.Any):
        raise TimeoutError(self.error_msg)

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
            import platform

            if platform.uname().system == "Windows":
                ...  # use threading
            else:
                ...  # use signal
                # signal.signal(signal.SIGALRM, handler)
                # Define a timeout for your function
                # signal.alarm(10)

            # use threading.join for this
            raise NotImplementedError

        async def async_timeout(*args, **kwargs):
            coro = func(*args, **kwargs)
            try:
                res = await asyncio.wait_for(coro, seconds)
            except TimeoutError as te:
                if logger:
                    logger.exception(f"{func} timeout after {seconds}s")
                raise te
            return res

        return async_timeout

    return decor_dispatch


if __name__ == "__main__":
    from loguru import logger

    @timeit(logger=logger, with_args=True, log_threshold=-1)
    def test_timeit(a: int, b: int, *, c: str, d: dict):
        return None

    test_timeit(3, 5, c="test", d={"name": "test"})
