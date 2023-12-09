import typing as ty
from functools import cached_property, singledispatchmethod

from src.app.actor import Actor, ActorRef, MailBox
from src.domain._log import logger
from src.domain.interface import IEvent, IEventStore, IMessage
from src.domain.model.base import Event


class Journal(Actor[ty.Any]):
    """
    Consumer that consumes events from event bus and persist them to event store
    """

    def __init__(
        self, eventstore: IEventStore, mailbox: MailBox, ref: ActorRef
    ) -> None:
        super().__init__(mailbox)
        self.system.subscribe_events(self)
        self.eventstore = eventstore
        self._ref = ref

    async def on_receive(self) -> None:
        message = await self.mailbox.get()
        if message is None:
            raise Exception("Mailbox is empty")

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
        await self.mailbox.put(event)
        await self.on_receive()

    @cached_property
    def ref(self) -> ActorRef:
        return self._ref

    async def list_events(self, ref: ActorRef) -> "list[IEvent]":
        return await self.eventstore.get(entity_id=ref)
