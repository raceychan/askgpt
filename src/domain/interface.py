import pathlib
import typing as ty

from src.domain.model.interface import (
    ICommand,
    Identifiable,
    IEntity,
    IEvent,
    IMessage,
    IQuery,
)
from src.domain.service.interface import IEngine, IEventStore, IRepository, IUnitOfWork

T = ty.TypeVar("T")

TState = ty.TypeVar("TState")
TEntity = ty.TypeVar("TEntity", bound=IEntity)

ActorRef = ty.Annotated[str, "AbstractActorRef", "ActorRef"]

SystemRef = ty.NewType("SystemRef", ActorRef)
EventLogRef = ty.NewType("EventLogRef", ActorRef)
JournalRef = ty.NewType("JournalRef", ActorRef)


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

    db: IDB

    class ActorRefs(ty.Protocol):
        SYSTEM: SystemRef = SystemRef("system")
        EVENTLOG: EventLogRef = EventLogRef("eventlog")
        JOURNAL: JournalRef = JournalRef("journal")

    actor_refs: ActorRefs
