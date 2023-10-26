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
        self.system._journal_started_event.set()

    async def on_receive(self):
        message = await self.mailbox.get()
        print("journal received")
        if isinstance(message, Event):
            await self.eventstore.add(message)
            print(f"{message} added to eventstore")
        else:
            raise TypeError("Currently journal only accepts events")

    async def handle(self, message: Message):
        ...

    async def persist_event(self):
        raise NotImplementedError

    async def start(self):
        await self.persist_event()

    async def apply(self, event: Event):
        raise NotImplementedError

    async def publish(self, event: Event):
        await self.receive(event)

    @classmethod
    def build(
        cls,
        *,
        db_url: str,
    ):
        es = EventStore.build(db_url=db_url)
        return cls(eventstore=es, mailbox=MailBox.build())
