import abc

"""
Remember:
repository and unitwork in doman service
should only be interfaces
and let infra implemente
"""


from src.domain.model import Event


class IEventStore(abc.ABC):
    @abc.abstractmethod
    async def add(self, event: Event):
        ...

    @abc.abstractmethod
    async def add_all(self, events: list[Event]):
        ...

    @abc.abstractmethod
    async def get(self, entity_id: str) -> list[Event]:
        ...

    @abc.abstractmethod
    async def remove(self, entity_id: str):
        ...


class IRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, entity):
        # Implement user creation logic here
        ...

    @abc.abstractmethod
    def update(self, entity):
        # Implement user update logic here
        ...

    @abc.abstractmethod
    def delete(self, entity):
        # Implement user deletion logic here
        ...

    def find_by_id(self, entity_id: str):
        # Implement finding a user by ID logic here
        ...


class UnitOfWork:
    """
    with UnitOfWork(engine) as uow:
        repo = UserRepository(uow.engine)
        user_repository.create(new_user)
        retrieved_user = user_repository.find_by_id(new_user.id)
        retrieved_user.name = "Updated John"
        user_repository.update(retrieved_user)
    """

    def __init__(self, engine):
        self.engine = engine

    def __enter__(self):
        self.transaction = self.engine.begin().__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.transaction.commit()
        else:
            self.transaction.rollback()
        self.transaction.close()
