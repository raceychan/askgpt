import asyncio
import typing as ty
from functools import cached_property, singledispatchmethod

from src.app.actor import Actor, ActorRef
from src.domain._log import logger
from src.domain.interface import IEvent, IEventStore, IMessage
from src.domain.model import Event
from src.infra.mq import MailBox


class Journal(Actor[ty.Any]):
    """
    Consumer that consumes events from event bus and persist them to event store
    """

    _loop: asyncio.AbstractEventLoop

    def __init__(
        self, eventstore: IEventStore, mailbox: MailBox, ref: ActorRef
    ) -> None:
        super().__init__(mailbox)
        self.system.subscribe_events(self)
        self.eventstore = eventstore
        self.__ref = ref

    async def on_receive(self) -> None:
        message = await self.mailbox.get()
        if isinstance(message, Event):
            logger.debug(f"Journal received event: {message}")
            await self.eventstore.add(message)
        else:
            raise NotImplementedError("Currently journal only accepts events")

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

    async def list_events(self, ref: ActorRef) -> "list[IEvent]":
        return await self.eventstore.get(entity_id=ref)
