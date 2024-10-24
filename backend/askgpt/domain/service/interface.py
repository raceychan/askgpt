import abc
import typing as ty

from askgpt.domain.interface import IEntity, IEvent
from askgpt.domain.model.base import Event

"""
Remember:
repository and unitwork in doman service
should only be interfaces
and let infra implemente
"""


class IEventStore(abc.ABC):
    @abc.abstractmethod
    async def add(self, event: Event) -> None: ...

    @abc.abstractmethod
    async def add_all(self, events: list[IEvent]) -> None: ...

    @abc.abstractmethod
    async def get(self, entity_id: str) -> list[IEvent]: ...

    @abc.abstractmethod
    async def remove(self, entity_id: str) -> None: ...


class IRepository[TEntity: IEntity](ty.Protocol):
    async def add(self, entity: TEntity) -> None:
        # Implement user creation logic here
        ...

    async def get(self, entity_id: str) -> TEntity | None:
        # Implement finding a user by ID logic here
        ...

    async def update(self, entity: TEntity) -> None:
        # Implement user update logic here
        ...

    async def remove(self, entity_id: str) -> None:
        # Implement user deletion logic here
        ...
