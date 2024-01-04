import contextlib
import inspect
import types
import typing as ty
from dataclasses import dataclass
from functools import update_wrapper, wraps
from time import perf_counter

from src.domain._log import logger


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
        return f"{self.location} {self.name}{str(self.signature)}"

    @classmethod
    def from_func(cls, func: ty.Callable):
        name = func.__name__
        func_code = func.__code__
        code = inspect.getsource(func)
        sig = inspect.signature(func)
        is_async = inspect.iscoroutinefunction(func)
        location = f"{func_code.co_filename}({func_code.co_firstlineno})"
        funcinfo = cls(
            name=name, code=code, signature=sig, location=location, is_async=is_async
        )
        return funcinfo


@dataclass(frozen=True, kw_only=True, slots=True, repr=False, unsafe_hash=True)
class MethodInfo[T](FuncInfo):
    owner: T
    onwer_cls: type[T]

    @classmethod
    def from_func(cls, func: ty.Callable):
        raise NotImplementedError("use from_method instead")

    @classmethod
    def from_method(cls, method: ty.Callable):
        ...


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


# class timeit:
#     def __init__(self, func):
#         self._func = func
#         self.funcinfo = FuncInfo.from_func(func)

#     def __set_name__(self, owner_cls, name):
#         self.name = name

#     def __get__(self, obj, obj_type):
#         return types.MethodType(self, obj) if obj else self

#     def __call__(self, *args, **kwargs):
#         wp = self.atimer if self.funcinfo.is_async else self.timer
#         return wp(*args, **kwargs)

#     def timer(self, *args, **kwargs):
#         start = perf_counter()
#         res = self._func(*args, **kwargs)
#         end = perf_counter()
#         exec_info = ExecInfo(
#             funcinfo=self.funcinfo,
#             args=args,
#             kwargs=kwargs,
#             timecost=end - start,
#             unit="s",
#         )
#         logger.info(exec_info.format_repr())
#         return res

#     async def atimer(self, *args, **kwargs):
#         start = perf_counter()
#         res = await self._func(*args, **kwargs)
#         end = perf_counter()
#         exec_info = ExecInfo(
#             funcinfo=self.funcinfo,
#             args=args,
#             kwargs=kwargs,
#             timecost=end - start,
#             unit="s",
#         )
#         logger.info(exec_info.format_repr())
#         return res


@ty.overload
def timeit[R, **P](func: ty.Callable[P, R]) -> ty.Callable[P, R]:
    ...


@ty.overload
def timeit[
    R, **P
](func: ty.Callable[P, ty.Awaitable[R]]) -> ty.Callable[P, ty.Awaitable[R]]:
    ...


def timeit[
    R, **P
](
    _func: ty.Optional[ty.Callable[P, R]] = None,
    *,
    unit: ty.Literal["ns", "ms", "s"] = "s",
    precision: int = 2,
    log_if: ty.Callable[[float], bool] = lambda x: x > 1,
    with_arguments: bool = False,
):
    def decorator(func: ty.Callable[P, R]) -> ty.Callable[P, R]:
        funcinfo = FuncInfo.from_func(func)

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs):
            start = perf_counter()
            res = func(*args, **kwargs)
            end = perf_counter()
            timecost = round(end - start, precision)
            exec_info = ExecInfo(
                funcinfo=funcinfo,
                args=args,
                kwargs=kwargs,
                timecost=timecost,
                unit=unit,
            )
            if log_if(timecost):
                logger.info(exec_info.format_repr())
            return res

        @wraps(func)
        async def awrapper(*args: P.args, **kwargs: P.kwargs):
            start = perf_counter()
            res = await func(*args, **kwargs)  # type: ignore
            end = perf_counter()
            timecost = round(end - start, precision)
            exec_info = ExecInfo(
                funcinfo=funcinfo,
                args=args,
                kwargs=kwargs,
                timecost=timecost,
                unit=unit,
            )
            if log_if(timecost):
                logger.info(exec_info.format_repr())
            return res

        return awrapper if inspect.iscoroutinefunction(func) else wrapper  # type: ignore

    if _func is None:
        return decorator
    else:
        return decorator(_func)
