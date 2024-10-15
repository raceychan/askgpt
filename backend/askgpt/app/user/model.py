from dataclasses import dataclass


@dataclass(frozen=True)
class UserInfo:
    entity_id: str
    email: str
    name: str


# class IUserRepository(IRepository[UserAuth]):
#     async def add(self, entity: UserAuth) -> None: ...

#     async def update(self, entity: UserAuth) -> None: ...

#     async def get(self, entity_id: str) -> UserAuth | None: ...

#     async def remove(self, entity_id: str) -> None: ...

#     async def list_all(self) -> list[UserAuth]: ...

#     async def search_user_by_email(self, useremail: str) -> UserAuth | None: ...
