import pathlib
import typing as ty

from .model.interface import ICommand, Identifiable, IEntity, IEvent, IMessage, IQuery
from .service.interface import IEngine, IEventStore, IRepository, IUnitOfWork

SystemRef = ty.NewType("SystemRef", str)
EventLogRef = ty.NewType("EventLogRef", str)
JournalRef = ty.NewType("JournalRef", str)


class ISettings(ty.Protocol):
    OPENAI_API_KEY: str

    class IDB(ty.Protocol):
        ...

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
