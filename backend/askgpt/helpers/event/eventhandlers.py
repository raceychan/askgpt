import asyncio
import typing as ty
from contextlib import asynccontextmanager
from functools import singledispatchmethod

from askgpt.helpers.event.eventbus import EventBus


class IEvent(ty.Protocol): ...


async def grease(gap: float = 0.1):
    """
    Pause for one event loop cycle.
    """
    await asyncio.sleep(gap)


class IMessageConsumer[IMessage](ty.Protocol):
    async def get(self) -> IMessage | None: ...


class EventListener:
    """
    Standalone event listener,
    polling events from a message queue and dispatching them to handlers.
    """

    def __init__(
        self,
        consumer: IMessageConsumer[IEvent],
        bus: EventBus,
        wait_gap: float = 0.1,
    ):
        self._consumer = consumer
        self._bus = bus
        self._wait_gap = wait_gap
        self.__main_task: asyncio.Task[ty.Any] | None = None

    async def _poll_forever(self):
        while True:
            try:
                message = await self._consumer.get()
                if message is None:
                    await grease(self._wait_gap)
                    continue
                await self._bus.dispatch_callback(message)
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

    @singledispatchmethod
    async def handle(self, event: IEvent):
        pass

    @handle.register
    async def handle_unknown(self, event: ty.Any) -> None:
        raise NotImplementedError(f"No handler for event {type(event)}")


async def main():
    # event_listener = EventListener(consumer=None, eventstore=None)
    # await event_listener.start()
    ...


if __name__ == "__main__":
    asyncio.run(main())
