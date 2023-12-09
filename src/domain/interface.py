import pathlib
import typing as ty

from src.domain.model.interface import ICommand as ICommand
from src.domain.model.interface import Identifiable as Identifiable
from src.domain.model.interface import IEntity as IEntity
from src.domain.model.interface import IEvent as IEvent
from src.domain.model.interface import IMessage as IMessage
from src.domain.model.interface import IQuery as IQuery
from src.domain.model.interface import utc_datetime as utc_datetime
from src.domain.service.interface import IEngine as IEngine
from src.domain.service.interface import IEventStore as IEventStore
from src.domain.service.interface import IRepository as IRepository
from src.domain.service.interface import IUnitOfWork as IUnitOfWork

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
