import asyncio

from askgpt.helpers.event.msgbus import IEvent, MessageBus
from askgpt.infra.eventstore import EventStore

FAQ = """
1. periodically poll DomainEventsTable, publish events to handlers
2.
case 1: remote-handler
    a. send event to mq
    b. when remote handler receives the event from mq, in a tranaction:
        b1. update DomainEventsTable and set dispatched_at to now
        b2. add event to EventTaskSchedule table
    c. commit message to mq
    d. do business logic
    e. update EventTaskSchedule as needed

case 2: in-process handler
    a. in a transaction:
        a1. update DomainEventsTable, set dispatched_at to now
        a2. add event to EventTaskSchedule table
    c. do business logic
    d. update EventTaskSchedule as needed
"""

FAQ2 = """
Do we have to create EventTaskSchedule table?
it depends, in your usecase, if:
1. event tasks usually do not fail,
2. should only be processed once
3. can be done immediately
then one EventLog table is enough.
you can use the MQ as EventTaskSchedule.
"""


class EventBus(MessageBus):

    def __init__(self, es: EventStore):
        super().__init__()
        self._es = es

    @property
    def es(self) -> EventStore:
        return self._es

    async def dispatch(self, event: IEvent, gather: bool = False):
        """
        Notify all subscribers of the event
        if gather is False, handlers would run in the background
        """
        tasks = [
            asyncio.create_task(handler(event))
            for handler in self.event_handlers[type(event)]
        ]
        if gather:
            await asyncio.gather(*tasks)

    async def dispatch_callback(self, event: IEvent):
        async with self._es.uow.trans():
            await self._es.transfer_event_to_task(event)

    async def collect_events(self):
        while True:
            await asyncio.sleep(600)
            events = await self._es.list_pending_events()
            for event in events:
                asyncio.create_task(self.dispatch(event))

    async def start(self):
        asyncio.create_task(self.collect_events())


"""
from askgpt.app.auth._model import UserSignedUp

bus = EventBus()  


@bus.register
async def example_handler(event: UserSignedUp, bus: EventBus) -> None:
    await bus.dispatch_callback(event)

    async with bus.es.uow.trans():
        # business logic here
        await bus.es.update_event_task_status(event)
"""
