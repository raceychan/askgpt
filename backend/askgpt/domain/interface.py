import typing as ty

from askgpt.domain.model.interface import ICommand as ICommand
from askgpt.domain.model.interface import Identifiable as Identifiable
from askgpt.domain.model.interface import IEntity as IEntity
from askgpt.domain.model.interface import IEvent as IEvent
from askgpt.domain.model.interface import IMessage as IMessage
from askgpt.domain.model.interface import IQuery as IQuery
from askgpt.domain.service.interface import IEngine as IEngine
from askgpt.domain.service.interface import IEventStore as IEventStore
from askgpt.domain.service.interface import IRepository as IRepository
from askgpt.domain.service.interface import IUnitOfWork as IUnitOfWork

type ActorRef = ty.Annotated[str, "AbstractActorRef", "ActorRef"]
SystemRef = ty.NewType("SystemRef", ActorRef)
EventLogRef = ty.NewType("EventLogRef", ActorRef)

type SQL_ISOLATIONLEVEL = ty.Literal[
    "SERIALIZABLE",
    "REPEATABLE READ",
    "READ COMMITTED",
    "READ UNCOMMITTED",
    "AUTOCOMMIT",
]


class AbstractActorRef(ty.Protocol): ...


class ISystem(ty.Protocol):
    """
    Singleton, should not be used directly, subclass it instead
    """

    def ensure_self(self) -> None:
        """Pre start events"""
        ...

    @property
    def settings(self): ...

    def ref(self) -> ActorRef: ...

    async def start(self) -> None: ...

    async def publish(self, event: IEvent) -> None: ...
