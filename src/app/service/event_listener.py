from src.app.actor import Actor
from src.domain.model import Event, Message
from src.infra.eventstore import EventStore
from src.infra.mq import MailBox


class EventRecord(Actor):
    def __init__(self, eventstore: EventStore, mailbox: MailBox):
        self.eventstore = eventstore
        self.mailbox = mailbox

    async def handle(self, message: Message):
        if not isinstance(message, Event):
            raise TypeError(f"Unexpected message type: {type(message)}")

        await self.eventstore.add(message)

    async def start(self):
        while self.mailbox:
            for msg in self.mailbox:
                await self.handle(msg)
