# import asyncio
# import typing as ty
# from dataclasses import dataclass


# @dataclass
# class Retry:
#     attempts: int
#     catch: type[Exception]
#     waittime_s: int
#     waittime_ms: int
#     waiter: ty.Callable

#     @property
#     def waittime(self) -> float:
#         return self.waittime_s * 1000 + self.waittime_ms


# def expo_waiter(attempt: int) -> float:
#     raise NotImplementedError


# def retry(
#     attmpts: int,
#     catch: type[Exception],
#     waittime_s: int,
#     waitime_ms: int,
#     waiter: function,
# ) -> ty.Callable[[ty.Callable], ty.Callable]:
#     def func_receiver(func):
#         def arg_receiver(*args, **kwargs):
#             return func(*args, **kwargs)

#         async def async_arg_receiver(*args, **kwargs):
#             return await func(*args, **kwargs)

#         if asyncio.iscoroutinefunction(func):
#             return async_arg_receiver
#         else:
#             return arg_receiver

#     return func_receiver
