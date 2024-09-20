# import asyncio
# import enum
# import warnings
# from types import TracebackType
# from typing import Optional, Type


# def _uncancel_task(task: "asyncio.Task[object]") -> None:
#     pass


# def timeout(delay: Optional[float]) -> "Timeout":
#     """
#     >>> async with timeout(0.001):
#     ...     async with aiohttp.get('https://github.com') as r:
#     ...         await r.text()
#     """

#     loop = asyncio.get_running_loop()
#     if delay is not None:
#         deadline = loop.time() + delay  # type: Optional[float]
#     else:
#         deadline = None
#     return Timeout(deadline, loop)


# class _State(enum.Enum):
#     INIT = "INIT"
#     ENTER = "ENTER"
#     TIMEOUT = "TIMEOUT"
#     EXIT = "EXIT"


# class Timeout:
#     __slots__ = ("_deadline", "_loop", "_state", "_timeout_handler", "_task")

#     def __init__(
#         self, deadline: Optional[float], loop: asyncio.AbstractEventLoop
#     ) -> None:
#         self._loop = loop
#         self._state = _State.INIT

#         self._task: Optional["asyncio.Task[object]"] = None
#         self._timeout_handler = None  # type: Optional[asyncio.Handle]
#         if deadline is None:
#             self._deadline = None  # type: Optional[float]
#         else:
#             self.update(deadline)

#     def __enter__(self) -> "Timeout":
#         warnings.warn(
#             "with timeout() is deprecated, use async with timeout() instead",
#             DeprecationWarning,
#             stacklevel=2,
#         )
#         self._do_enter()
#         return self

#     def __exit__(
#         self,
#         exc_type: Optional[Type[BaseException]],
#         exc_val: Optional[BaseException],
#         exc_tb: Optional[TracebackType],
#     ) -> Optional[bool]:
#         self._do_exit(exc_type)
#         return None

#     async def __aenter__(self) -> "Timeout":
#         self._do_enter()
#         return self

#     async def __aexit__(
#         self,
#         exc_type: Optional[Type[BaseException]],
#         exc_val: Optional[BaseException],
#         exc_tb: Optional[TracebackType],
#     ) -> Optional[bool]:
#         self._do_exit(exc_type)
#         return None

#     @property
#     def expired(self) -> bool:
#         """Is timeout expired during execution?"""
#         return self._state == _State.TIMEOUT

#     @property
#     def deadline(self) -> Optional[float]:
#         return self._deadline

#     def reject(self) -> None:
#         """Reject scheduled timeout if any."""
#         # cancel is maybe better name but
#         # task.cancel() raises CancelledError in asyncio world.
#         if self._state not in (_State.INIT, _State.ENTER):
#             raise RuntimeError(f"invalid state {self._state.value}")
#         self._reject()

#     def _reject(self) -> None:
#         self._task = None
#         if self._timeout_handler is not None:
#             self._timeout_handler.cancel()
#             self._timeout_handler = None

#     def shift(self, delay: float) -> None:
#         deadline = self._deadline
#         if deadline is None:
#             raise RuntimeError("cannot shift timeout if deadline is not scheduled")
#         self.update(deadline + delay)

#     def update(self, deadline: float) -> None:
#         if self._state == _State.EXIT:
#             raise RuntimeError("cannot reschedule after exit from context manager")
#         if self._state == _State.TIMEOUT:
#             raise RuntimeError("cannot reschedule expired timeout")
#         if self._timeout_handler is not None:
#             self._timeout_handler.cancel()
#         self._deadline = deadline
#         if self._state != _State.INIT:
#             self._reschedule()

#     def _reschedule(self) -> None:
#         assert self._state == _State.ENTER
#         deadline = self._deadline
#         if deadline is None:
#             return

#         now = self._loop.time()
#         if self._timeout_handler is not None:
#             self._timeout_handler.cancel()

#         self._task = asyncio.current_task()
#         if deadline <= now:
#             self._timeout_handler = self._loop.call_soon(self._on_timeout)
#         else:
#             self._timeout_handler = self._loop.call_at(deadline, self._on_timeout)

#     def _do_enter(self) -> None:
#         if self._state != _State.INIT:
#             raise RuntimeError(f"invalid state {self._state.value}")
#         self._state = _State.ENTER
#         self._reschedule()

#     def _do_exit(self, exc_type: Optional[Type[BaseException]]) -> None:
#         if exc_type is asyncio.CancelledError and self._state == _State.TIMEOUT:
#             assert self._task is not None
#             _uncancel_task(self._task)
#             self._timeout_handler = None
#             self._task = None
#             raise asyncio.TimeoutError
#         # timeout has not expired
#         self._state = _State.EXIT
#         self._reject()
#         return None

#     def _on_timeout(self) -> None:
#         assert self._task is not None
#         self._task.cancel()
#         self._state = _State.TIMEOUT
#         # drop the reference early
#         self._timeout_handler = None
