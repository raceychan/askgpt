from sqlalchemy import Engine, Transaction

"""
Remember:
repository and unitwork in doman service
should only be interfaces
and let infra implemente
"""


class Repository:
    def __init__(self, engine):
        self.engine = engine

    def add(self, user):
        # Implement user creation logic here
        ...

    def update(self, user):
        # Implement user update logic here
        ...

    def delete(self, user):
        # Implement user deletion logic here
        ...

    def find_by_id(self, user_id):
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

    def __init__(self, engine: Engine):
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
