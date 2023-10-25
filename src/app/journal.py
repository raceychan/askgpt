import asyncio

from src.app.actor import Actor
from src.domain.model import Event, Message
from src.infra.eventstore import EventStore
from src.infra.mq import MailBox


class Journal(Actor):
    _loop: asyncio.AbstractEventLoop

    def __init__(self, eventstore: EventStore, mailbox: MailBox):
        super().__init__(mailbox)
        self.eventstore = eventstore

    async def on_receive(self):
        raise NotImplementedError

    async def handle(self, message: Message):
        if not isinstance(message, Event):
            raise TypeError(f"Unexpected message type: {type(message)}")

        await self.eventstore.add(message)

    async def _setup(self):
        self._loop = asyncio.get_running_loop()

    async def persist_event(self):
        if self.mailbox.size() == 0:
            await asyncio.sleep(1)
            await self.persist_event()
        else:
            for msg in self.mailbox:
                await self.handle(msg)

    async def start(self):
        await self._setup()
        await self.persist_event()

    async def apply(self, event: Event):
        raise NotImplementedError

    @classmethod
    def build(
        cls,
        *,
        db_url: str,
    ):
        es = EventStore.build(db_url=db_url)
        return cls(eventstore=es, mailbox=MailBox.build())
