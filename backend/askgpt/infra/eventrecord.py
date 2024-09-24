import asyncio
import typing as ty
from contextlib import asynccontextmanager

from askgpt.adapters.queue import MessageConsumer
from askgpt.infra._log import logger
from askgpt.domain.interface import IEvent
from askgpt.infra.eventstore import EventStore


async def grease(gap: float = 0.1):
    """
    Pause for one event loop cycle.
    """
    await asyncio.sleep(gap)


class EventRecord:
    def __init__(
        self,
        consumer: MessageConsumer[IEvent],
        eventstore: EventStore,
        wait_gap: float = 0.1,  # in production this should be close to 0
    ):
        self._consumer = consumer
        self._eventstore = eventstore
        self._wait_gap = wait_gap
        self.__main_task: asyncio.Task[ty.Any] | None = None

    async def _poll_forever(self):
        while True:
            try:
                message = await self._consumer.get()
                if message is None:
                    await grease(self._wait_gap)
                    continue
                await self._eventstore.add(message)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("Unhandled exception in event record", exc_info=e)

    async def start(self):
        logger.info("started collecting event record")
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
                logger.info("stopped collecting event record")
                self.__main_task = None

    @asynccontextmanager
    async def lifespan(self):
        try:
            await self.start()
            yield self
        finally:
            await self.stop()
