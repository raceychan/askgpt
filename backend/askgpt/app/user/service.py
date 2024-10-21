from askgpt.infra.eventstore import EventStore

from ._model import UserInfo
from ._repository import UserRepository


class UserService:
    def __init__(self, user_repo: UserRepository, event_store: EventStore):
        self._user_repo = user_repo
        self._event_store = event_store
        self._uow = self._user_repo.uow

    async def get_user(self, user_id: str) -> UserInfo | None:
        async with self._uow.trans():
            return await self._user_repo.get(user_id)

    async def find_user(self, email: str) -> UserInfo | None:
        async with self._uow.trans():
            user_or_none = await self._user_repo.search_user_by_email(email)
        return user_or_none
