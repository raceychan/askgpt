import abc
import typing as ty
from types import TracebackType

from ..interface import IEntity
from ..model import Event

"""
Remember:
repository and unitwork in doman service
should only be interfaces
and let infra implemente
"""


class IEventStore(abc.ABC):
    @abc.abstractmethod
    async def add(self, event: Event) -> None:
        ...

    @abc.abstractmethod
    async def add_all(self, events: list[Event]) -> None:
        ...

    @abc.abstractmethod
    async def get(self, entity_id: str) -> list[Event]:
        ...

    @abc.abstractmethod
    async def remove(self, entity_id: str) -> None:
        ...


class IRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, entity: IEntity) -> None:
        # Implement user creation logic here
        ...

    @abc.abstractmethod
    def update(self, entity: IEntity) -> None:
        # Implement user update logic here
        ...

    @abc.abstractmethod
    def delete(self, entity: IEntity) -> None:
        # Implement user deletion logic here
        ...

    @abc.abstractmethod
    def get(self, entity_id: str) -> IEntity:
        # Implement finding a user by ID logic here
        ...


class IEngine(ty.Protocol):
    ...

    def begin(self) -> ty.Self:
        return self

    def __enter__(self) -> ty.Self:
        return self

    def commit(self) -> None:
        ...

    def rollback(self) -> None:
        ...

    def close(self) -> None:
        ...


class IUnitOfWork(abc.ABC):
    """
    with UnitOfWork(engine) as uow:
        repo = UserRepository(uow.engine)
        user_repository.create(new_user)
        retrieved_user = user_repository.find_by_id(new_user.id)
        retrieved_user.name = "Updated John"
        user_repository.update(retrieved_user)
    """

    def __init__(self, engine: IEngine):
        self.engine = engine

    def __enter__(self) -> ty.Self:
        self.transaction = self.engine.begin().__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException,
        traceback: TracebackType,
    ) -> None:
        if exc_type is None:
            self.transaction.commit()
        else:
            self.transaction.rollback()
        self.transaction.close()
