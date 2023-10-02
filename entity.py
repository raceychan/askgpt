import abc
import typing

from functools import partial
from uuid import uuid4
from dataclasses import dataclass, field

from sqlalchemy import (
    Table,
    Column,
    String,
    Boolean,
    create_engine,
    event,
)
from sqlalchemy.orm import registry, Session


@dataclass
class ABCCommand(abc.ABC):
    ...


@dataclass
class ABCEvent(abc.ABC):
    ...


@dataclass
class ABCEntity(abc.ABC):
    _events: list["ABCEvent"] = field(default_factory=list)

    def raise_event(self, event: "ABCEvent"):
        self._events.append(event)

    def get_events(self) -> typing.Iterable:
        return iter(self._events)

    def clear_events(self):
        self._events.clear()


@dataclass
class MakeCustomerPreferred(ABCCommand):
    customer_id: str


@dataclass
class ChangeCustomerLocale(ABCCommand):
    customer_id: str
    locale: str


@dataclass
class CreateCustomer(ABCCommand):
    customer: "Customer"


@dataclass
class EditCustomerDetails(ABCCommand):
    customer_detail: "CustomerDetail"


@dataclass
class CustomerCreated(ABCEvent):
    customer_id: str


@dataclass
class CustomerIsPreferred(ABCEvent):
    custom_id: str


from functools import singledispatchmethod


class EventHandler:
    def __init__(self, has_been_called: bool = False):
        self.has_been_called = has_been_called

    @singledispatchmethod
    def handle(self, event: "ABCEvent"):
        ...

    @handle.register
    def _(self, event: CustomerIsPreferred):
        self.has_been_called = True
        return


@dataclass
class Customer(ABCEntity):
    customer_id: str = field(default_factory=lambda: str(uuid4()))
    is_preferred: bool = field(default=False)

    def preferred(self):
        if self.is_preferred is False:
            self.is_preferred = True
            self.raise_event(CustomerIsPreferred(self.customer_id))


class Mediator:
    def __init__(self, event_handler: EventHandler):
        self.event_handler = event_handler

    def publish(self, event):
        self.event_handler.handle(event)


def map_table(model: type[Customer] = Customer):
    mapper_registry = registry()

    customer_table = Table(
        "customer",
        mapper_registry.metadata,
        Column("customer_id", String, primary_key=True),
        Column("is_preferred", Boolean),
    )

    mapper_registry.map_imperatively(Customer, customer_table)
    return mapper_registry


# @event.listens_for(Session, "before_commit")
def collect_event(session: Session, mailbox: Mediator):
    entity = next(iter(session.new))
    events = entity.get_events()
    for e in events:
        mailbox.publish(e)


def domain_entity_test():
    engine = create_engine("sqlite:///:memory:", echo=False, future=True)
    session = Session(bind=engine)

    mapper_registry = map_table()
    mapper_registry.metadata.create_all(engine)

    handler = EventHandler()
    mailbox = Mediator(event_handler=handler)

    event.listen(session, "before_commit", partial(collect_event, mailbox=mailbox))

    entity = Customer()

    with session.begin():
        session.add(entity)

        entity.preferred()
        session.commit()

    assert handler.has_been_called is True

    tables = mapper_registry.metadata.tables
    customer_table = tables["customer"]
    query = customer_table.select().where(
        customer_table.c.customer_id == entity.customer_id
    )

    result = session.execute(query).fetchall()
    # assert not result


if __name__ == "__main__":
    domain_entity_test()
