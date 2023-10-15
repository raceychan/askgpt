import asyncio

from src.app.actor import Actor
from src.domain.model import Event, Message
from src.infra.eventstore import EventStore
from src.infra.mq import MailBox


class EventRecord(Actor):
    _loop: asyncio.AbstractEventLoop

    def __init__(self, eventstore: EventStore, mailbox: MailBox):
        self.eventstore = eventstore
        self.mailbox = mailbox

    async def handle(self, message: Message):
        if not isinstance(message, Event):
            raise TypeError(f"Unexpected message type: {type(message)}")

        await self.eventstore.add(message)

    async def _setup(self):
        self._loop = asyncio.get_running_loop()

    async def persist_event(self):
        if not self.mailbox:
            await asyncio.sleep(1)
            # waiter = self._loop.create_future()
            # self._loop.call_later(0.1, waiter.set_result, None)
            # await waiter
            await self.persist_event()
        else:
            for msg in self.mailbox:
                await self.handle(msg)

    async def start(self):
        await self._setup()
        await self.persist_event()
