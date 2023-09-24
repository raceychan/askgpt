import typing
import abc
import queue
from uuid import uuid4
from datetime import datetime

import openai
import sqlalchemy as sa

from rich.console import Console
from pydantic import BaseModel, Field, computed_field

console = Console()


def read_env(filename: str = ".env") -> dict[str, typing.Any]:
    from pathlib import Path

    file = Path(__file__).parent / filename
    if not file.exists():
        raise Exception(f"{filename} file not found")

    def parse(val: str):
        if val[0] in {'"', "'"}:  # Removing quotes if they exist
            if val[0] == val[-1]:
                value = val[1:-1]
            else:
                raise ValueError(f"{val} inproperly quoted")

        # Type casting
        if val.isdecimal():
            value = int(val)  # Integer type
        elif val.lower() in {"true", "false"}:
            value = val.lower() == "true"  # Boolean type
        else:
            if val[0].isdecimal():  # Float type
                try:
                    value = float(val)
                except ValueError as ve:
                    pass
                else:
                    return value
            value = val  # Otherwise, string type
        return value

    config = {}
    ln = 1

    with file.open() as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                try:
                    key, value = line.split("=", 1)
                    config[key.strip()] = parse(value.strip())
                except ValueError as ve:
                    raise Exception(f"Invalid env line number {ln}: {line}") from ve
            ln += 1
    return config


class Receivable(typing.Protocol):
    def receive(self, message):
        ...


class MessageBroker(abc.ABC):
    @abc.abstractmethod
    def __len__(self) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def put(self, message):
        raise NotImplementedError

    @abc.abstractmethod
    def get(self):
        raise NotImplementedError

    @abc.abstractproperty
    def maxsize(self) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def register(self, subscriber: Receivable):
        raise NotImplementedError

    def broadcast(self, message):
        """
        Optional method to broadcast message to all subscribers,
        only push-based MQ should implement this method
        reff:
            https://stackoverflow.com/questions/39586635/why-is-kafka-pull-based-instead-of-push-based
        """
        raise NotImplementedError


class QueueBroker(MessageBroker):
    def __init__(self, maxsize=0):
        self._queue = queue.Queue(maxsize)
        self._maxsize = maxsize
        self._subscribers: set[Receivable] = set()

    def __len__(self):
        return len(self._queue.queue)

    @property
    def maxsize(self):
        return self._maxsize

    @property
    def subscribes(self):
        return self._subscribers.copy()

    def put(self, event: "Event"):
        self._queue.put(event)

    def get(self):
        return self._queue.get()

    def broadcast(self):
        while self:
            message = self.get()
            for subscriber in self._subscribers:
                subscriber.receive(message)

    def register(self, subscriber: Receivable):
        self._subscribers.add(subscriber)


class MailBox:
    def __init__(self, broker: MessageBroker):
        self._broker = broker

    def __len__(self):
        return len(self._broker)

    def __bool__(self):
        return self.__len__() > 0

    def put(self, event: "Event"):
        self._broker.put(event)

    def get(self):
        return self._broker.get()

    @property
    def volume(self):
        return self._broker.maxsize

    def register(self, subscriber: Receivable):
        self._broker.register(subscriber)


# ================== Domain Modeling ==================


def rich_repr(namespace: typing.Mapping, indent="\t"):
    lines = ""
    for key, val in namespace.items():
        if not key.startswith("_"):
            if isinstance(val, dict):
                lines += f"{indent}{key}=\n" + rich_repr(val, indent + indent)
            elif hasattr(val, "__dict__"):
                lines += f"{indent}{key}=\n" + rich_repr(val.__dict__, indent + indent)
            else:
                lines += f"{indent}{key}={val}\n"
    return lines


def uuid_factory():
    return str(uuid4())


class DomainBase(BaseModel):
    def to_json(
        self,
        indent: int | None = None,
        include: set | None = None,
        exclude: set | None = None,
        by_alias: bool = True,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
    ):
        return self.model_dump_json(
            indent=indent,
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
        )

    @classmethod
    def model_all_fields(cls) -> dict[str, type]:
        field_map = dict()
        computed_fields = cls.model_computed_fields.fget(cls)
        for fname, finfo in computed_fields.items():
            ftype = finfo.wrapped_property.fget.__annotations__["return"]
            if issubclass(ftype, DomainBase):
                field_map[fname] = ftype.model_all_fields()
            field_map[fname] = ftype

        for fname, finfo in cls.model_fields.items():
            ftype = finfo.annotation
            if issubclass(ftype, DomainBase):
                field_map[fname] = ftype.model_all_fields()

            field_map[fname] = finfo.annotation
        return field_map


class Entity(DomainBase):
    ...


class Command(DomainBase):
    ...


EventVersion: str = "1.0.0"


class Event(DomainBase):
    version: typing.ClassVar[str] = EventVersion
    entity_id: str
    timestamp: datetime = Field(default_factory=datetime.now)

    @computed_field
    @property
    def event_id(self) -> str:
        return str(uuid4())

    @event_id.setter
    def event_id(self, event_id):
        self.event_id = event_id

    @computed_field
    @property
    def event_type(self) -> str:
        return self.__class__.__name__.lower()


class Envelope(DomainBase):
    event: Event = Field(alias="payload")

    @computed_field
    def event_id(self) -> str:
        return self.event.event_id

    @computed_field
    def event_type(self) -> str:
        return self.event.event_type

    @computed_field(alias="aggregate_id")
    def entity_id(self) -> str:
        return self.event.entity_id

    @computed_field
    def timestamp(self) -> datetime:
        return self.event.timestamp

    @computed_field
    def version(self) -> str:
        return self.event.version


class DomainEvent:
    __tablename__: typing.ClassVar[str] = "domain_events"

    @classmethod
    def table_clause(cls) -> sa.TableClause:
        table = sa.table(
            cls.__tablename__,
            sa.column("id"),
            sa.column("event_id", sa.String),
            sa.column("payload", sa.JSON),
            sa.column("aggregate_id", sa.String),
            sa.column("status", sa.String),
            sa.column("version", sa.String),
        )
        return table


class Ask(DomainBase):
    question: str
    ask_id: str = Field(default_factory=uuid_factory)
    answer: str = Field(default="")

    @property
    def is_answered(self):
        return self.answer != ""

    def set_answer(self, answer: str):
        self.answer = answer

    def __repr__(self):
        return f"{self.__class__.__name__}(ask_id={self.ask_id}, question={self.question}, answer={self.answer})"


class AskQuestion(Command):
    ask: Ask


class AskAnswered(Event):
    history_id: str = Field(alias="entity_id")
    ask: Ask

    @computed_field
    @property
    def event_id(self) -> str:
        return self.ask.ask_id


class AskHistory(Entity):
    history_id: str = Field(default_factory=uuid_factory)
    history: dict[str, Ask] = Field(default_factory=dict)

    def query_ask(self, ask_id: str):
        return self.history[ask_id]

    def add_ask(self, ask: Ask):
        self.history[ask.ask_id] = ask

    def answer_ask(self, ask_id: str, answer: str):
        self.history[ask_id].set_answer(answer)

    def as_context(self):
        for ask in self.history.values():
            yield dict(role="assistant", content=ask.question)
            if ask.is_answered:
                yield dict(role="professor", content=ask.answer)

    def __repr__(self):
        lines = rich_repr(self.__dict__)
        return f"{self.__class__.__name__}(\t\n{lines})"


# ================== Application ==================


class Actor(abc.ABC):
    def _handle(self, command: Command):
        "Process message"

    def send(self, message, actor: "Actor"):
        "Send message to other actor, message may contain information about sender id"
        actor.receive(message)

    def receive(self, message: Command):
        "Receive message from other actor, may either persist or handle message or both"
        self._handle(message)

    def create(self) -> "Actor":
        "Create new actor"
        ...


class Studet(Actor):
    def __init__(self, history: AskHistory):
        self.history = history

    def send(self, cmd: Command, professor: Actor):
        professor.receive(cmd)

    def ask(self, question: str, professor: Actor):
        ask = Ask(question)
        cmd = AskQuestion(ask)

        self.history.add_ask(ask)
        self.send(cmd, professor)


class Professor(Actor):
    def __init__(
        self, history: AskHistory, mailbox: MailBox, kb: openai.ChatCompletion
    ):
        self.history = history
        self.mailbox = mailbox
        self.kb = kb

    def answer(self, ask: Ask):
        context = self.history.as_context()
        model = "gpt-3.5-turbo"
        try:
            chat_resp = self.kb.create(model=model, stream=True, messages=context)
        except Exception as e:
            raise e
        else:
            console.print("question sent to openai")

        console.rule("[bold red]Answer")
        console.print("")

        answer = ""
        for resp in chat_resp:
            for choice in resp.choices:  # type: ignore
                content = choice.get("delta", {}).get("content")
                if content:
                    answer += content
                    console.print(content, end="")
        self.history.answer_ask(ask.ask_id, answer)
        print(f"{ask} is answerd: {answer}")
        return answer

    def _handle(self, command: Command):
        if isinstance(command, AskQuestion):
            self.answer(command.ask)
            self.publish(
                AskAnswered(history_id=self.history.history_id, ask=command.ask)  # type: ignore
            )

    def publish(self, event: Event):
        self.mailbox.put(event)


# ================== Event Store ==================
# from sqlalchemy.orm import sessionmaker


def map_table():
    from sqlalchemy.orm import registry

    mapper_registry = registry()

    domain_events_table = sa.Table(
        "domain_events",
        mapper_registry.metadata,
        sa.Column("customer_id", sa.String, primary_key=True),
        sa.Column("is_preferred", sa.Boolean),
    )

    mapper_registry.map_imperatively(Envelope, domain_events_table)

    return mapper_registry


class EventStore(Actor):
    def __init__(self, engine: sa.Engine):
        # self.session_maker = sessionmaker(engine)
        self.engine = engine

    def _handle(self, event: Event):
        self.add(event)

    def add(self, event: "Event"):
        sqlstr = """--sql
        INSERT INTO 
        domain_events (
            id,
            event_type,
            event_body,
            aggregate_id,
            status,
            version,
            created_at,
            updated_at
        ) VALUES (
            :event_id,
            :event_type,
            :event_body,
            :entity_id,
            :status,
            :version,
            :timestamp,
            :timestamp
        )
        """

        stmt = sa.text(sqlstr).bindparams(
            # event_id=event.event_id,
            # event_type=event.event_type,
            # event_body=event.to_json(),
            # entity_id=event.entity_id,
            # status="new",
        )

        # session = self.session_maker()
        # with session.begin():
        #     session.add(event)
        #     session.commit()

    def add_all(self, events: list["Event"]):
        ...
        # session = self.session_maker()
        # with session.begin():
        #     session.add_all(events)
        #     session.commit()

    def get(self, entity_id: str) -> list["Event"]:
        sqlstr = """--sql
        SELECT
            id,
            event_type,
            event_body,
            aggregate_id,
            status,
            version,
            created_at,
            updated_at
        FROM
            domain_events
        WHERE
            aggregate_id =: entity_id
        """

        stmt = sa.text(sqlstr).bindparams(entity_id=entity_id)

        # session = self.session_maker()
        # with session.begin():
        #     result = session.execute(stmt)
        #     rows = result.all()
        #     events = [row[0] for row in rows]
        return events

    def remove(self, entity_id: str):
        sqlstr = """--sql
        DELETE FROM 
            domain_events
        WHERE 
            aggregate_id = :entity_id
        """
        stmt = sa.text(sqlstr).bindparams(entity_id=entity_id)

        # session = self.session_maker()
        # with session.begin():
        #     session.execute(stmt)
        #     session.commit()


# ================== Event Store ==================


def main():
    config = read_env()
    history = AskHistory()
    mailbox = MailBox(QueueBroker())

    db_url = "database/eventstore.db"
    engine = sa.create_engine(f"sqlite+aiosqlite:///{db_url}:", echo=True)

    es = EventStore(engine)
    mailbox.register(es)

    professor = Professor(
        history, mailbox, kb=openai.ChatCompletion(api_key=config["OPENAI_API_KEY"])
    )
    student = Studet(history)

    while True:
        question = input("what is your problem?\n")
        student.ask(question, professor)


if __name__ == "__main__":
    main()
