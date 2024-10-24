import typing as ty

from askgpt.domain.model.interface import ICommand as ICommand
from askgpt.domain.model.interface import Identifiable as Identifiable
from askgpt.domain.model.interface import IEntity as IEntity
from askgpt.domain.model.interface import IEvent as IEvent
from askgpt.domain.model.interface import IMessage as IMessage
from askgpt.domain.model.interface import IQuery as IQuery
from askgpt.domain.service.interface import IEventStore as IEventStore
from askgpt.domain.service.interface import IRepository as IRepository

type ActorRef = ty.Annotated[str, "AbstractActorRef", "ActorRef"]
SystemRef = ty.NewType("SystemRef", ActorRef)
EventLogRef = ty.NewType("EventLogRef", ActorRef)
