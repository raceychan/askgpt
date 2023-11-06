import asyncio
import typing as ty
from functools import singledispatchmethod

from src.domain import Event
from src.domain.interface import IEvent, IMessage
from src.infra import EventStore, MailBox

from .actor import Actor


class Journal(Actor):
    _loop: asyncio.AbstractEventLoop

    def __init__(self, eventstore: EventStore, mailbox: MailBox) -> None:
        super().__init__(mailbox)
        self.eventstore = eventstore
        self.system.eventlog.register_listener(self)

    async def on_receive(self) -> None:
        message = await self.mailbox.get()
        if isinstance(message, Event):
            await self.eventstore.add(message)
        else:
            raise TypeError("Currently journal only accepts events")

    @singledispatchmethod
    async def handle(self, message: IMessage) -> None:
        raise NotImplementedError

    async def persist_event(self) -> None:
        raise NotImplementedError

    async def start(self) -> None:
        await self.persist_event()

    @singledispatchmethod
    def apply(self, event: IEvent) -> ty.Self:
        raise NotImplementedError

    async def publish(self, event: IEvent) -> None:
        raise NotImplementedError

    @classmethod
    def build(
        cls,
        *,
        db_url: str,
    ) -> ty.Self:
        es = EventStore.build(db_url=db_url)
        return cls(eventstore=es, mailbox=MailBox.build())
