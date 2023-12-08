import asyncio
import typing as ty
from contextlib import asynccontextmanager

from src.domain._log import logger
from src.domain.interface import IEvent
from src.infra.eventstore import EventStore
from src.infra.mq import BaseConsumer


class EventRecord:
    # TODO: this should replcae Actor.EventLog and Actor.Journal at somepoint in the future
    def __init__(
        self, consumer: BaseConsumer[IEvent], es: EventStore, wait_gap: float = 0.1
    ):
        self._consumer = consumer
        self._es = es
        self._wait_gap = wait_gap
        self.__main_task: asyncio.Task[ty.Any] | None = None

    async def _poll_forever(self):
        wait_gap = self._wait_gap
        while True:
            try:
                message = await self._consumer.get()
                if message is None:
                    await asyncio.sleep(wait_gap)
                    continue
                await self._es.add(message)
            except asyncio.CancelledError:
                break

    async def start(self):
        if self.__main_task is None or self.__main_task.done():
            self.__main_task = asyncio.create_task(self._poll_forever())

    async def stop(self):
        if self.__main_task is not None:
            self.__main_task.cancel()
            try:
                await self.__main_task
            except asyncio.CancelledError:
                pass  # Task cancellation is expected
            finally:
                self.__main_task = None

    @asynccontextmanager
    async def lifespan(self):
        try:
            await self.start()
            yield self
        finally:
            await self.stop()
