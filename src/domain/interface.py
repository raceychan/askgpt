import pathlib
import typing as ty

from src.domain.model.interface import (
    ICommand,
    Identifiable,
    IEntity,
    IEvent,
    IMessage,
    IQuery,
    utc_datetime,
)
from src.domain.service.interface import IEngine, IEventStore, IRepository, IUnitOfWork

ActorRef = ty.Annotated[str, "AbstractActorRef", "ActorRef"]
SystemRef = ty.NewType("SystemRef", ActorRef)
EventLogRef = ty.NewType("EventLogRef", ActorRef)
JournalRef = ty.NewType("JournalRef", ActorRef)

type SQL_ISOLATIONLEVEL = ty.Literal[
    "SERIALIZABLE",
    "REPEATABLE READ",
    "READ COMMITTED",
    "READ UNCOMMITTED",
    "AUTOCOMMIT",
]


class AbstractActorRef(ty.Protocol):
    ...


class ISettings(ty.Protocol):
    OPENAI_API_KEY: str

    class IDB(ty.Protocol):
        @property
        def DB_URL(self) -> str:
            ...

        @property
        def ASYNC_DB_URL(self) -> str:
            ...

        DB_DRIVER: str
        DATABASE: pathlib.Path
        ENGINE_ECHO: bool
        ISOLATION_LEVEL: SQL_ISOLATIONLEVEL

    db: IDB

    class IActorRefs(ty.Protocol):
        SYSTEM: SystemRef
        EVENTLOG: EventLogRef
        JOURNAL: JournalRef

    actor_refs: IActorRefs
