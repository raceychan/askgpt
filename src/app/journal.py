import asyncio
import typing as ty
from functools import cached_property, singledispatchmethod

from src.app.actor import Actor, ActorRef
from src.app.interface import IJournal
from src.domain.interface import IEvent, IEventStore, IMessage
from src.domain.model import Event
from src.infra.eventstore import EventStore
from src.infra.mq import MailBox


class Journal(Actor[ty.Any], IJournal):
    _loop: asyncio.AbstractEventLoop

    def __init__(
        self, eventstore: IEventStore, mailbox: MailBox, ref: ActorRef
    ) -> None:
        super().__init__(mailbox)
        self.eventstore = eventstore
        self.system.eventlog.register_listener(self)
        self.__ref = ref

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

    @cached_property
    def ref(self) -> ActorRef:
        return self.__ref

    @classmethod
    def build(
        cls,
        *,
        db_url: str,
        ref: ActorRef,
    ) -> ty.Self:
        es = EventStore.build(db_url=db_url)
        return cls(eventstore=es, mailbox=MailBox.build(), ref=ref)

    async def list_events(self, ref: ActorRef) -> "list[IEvent]":
        return await self.eventstore.get(entity_id=ref)
