import typing as ty
from contextlib import asynccontextmanager

from src.app.bootstrap import bootstrap
from src.app.gpt import model, repository
from src.app.gpt.system import (
    Authenticator,
    GPTSystem,
    SessionActor,
    SystemState,
    UserActor,
)
from src.domain import encrypt
from src.domain._log import logger
from src.domain.config import Settings
from src.infra.eventstore import EventStore
from src.infra.mq import MailBox
from src.infra.sa_utils import async_engine_factory


class GPTService:
    def __init__(
        self,
        system: GPTSystem,
        user_repo: repository.UserRepository,
        session_repo: repository.SessionRepository,
    ):
        self._service_state = SystemState.created
        self._system = system
        self._user_repo = user_repo
        self._session_repo = session_repo

    @property
    def system(self) -> GPTSystem:
        return self._system  # type: ignore

    @property
    def state(self) -> SystemState:
        return self._service_state

    @state.setter
    def state(self, state: SystemState) -> None:
        if self._service_state is SystemState.stopped:
            raise Exception("system already stopped")
        self._service_state = state

    async def send_question(
        self, auth: Authenticator, session_id: str, question: str
    ) -> None:
        user_actor = await self.system.rebuild_user(auth.user_id)

        if session_id not in user_actor.entity.session_ids:
            session_actor = await self.user_create_session(
                user_actor.entity_id, session_id
            )
        else:
            session_actor = await user_actor.rebuild_session(session_id)

        command = model.SendChatMessage(
            user_id=auth.user_id,
            session_id=session_id,
            message_body=question,
            role="user",
        )

        await session_actor.receive(command)

    async def interactive(self, auth: Authenticator, session_id: str) -> None:
        while True:
            question = input("\nwhat woud you like to ask?\n\n")
            await self.send_question(auth, session_id, question)

    async def login(self, email: str, password: str) -> Authenticator:
        if not email:
            raise ValueError("email is required")

        user = await self._user_repo.search_user_by_email(email)

        if not user:
            raise ValueError("user not found")

        if not user.user_info.verify_password(password):
            raise ValueError("Invalid password")

        logger.success(f"User {user} logged in")
        auth = Authenticator(user_id=user.entity_id)
        auth.authenticate()
        return auth

    async def create_user(
        self, username: str, useremail: str, password: str
    ) -> UserActor:
        user_info: model.UserInfo = model.UserInfo(
            user_name=username,
            user_email=useremail,
            hash_password=encrypt.hash_password(password.encode()),
        )
        user_id = model.uuid_factory()
        create_user = model.CreateUser(user_id=user_id, user_info=user_info)
        await self.system.receive(create_user)
        return self.system.select_child(user_id)

    async def user_create_session(self, user_id: str, session_id: str) -> SessionActor:
        user_actor = self.system.select_child(user_id)

        await user_actor.handle(
            model.CreateSession(user_id=user_id, session_id=session_id)
        )
        return user_actor.select_child(session_id)

    async def find_user(self, username: str, useremail: str) -> model.User | None:
        """
        make sure user does not exist
        """
        user_or_none = await self._user_repo.search_user_by_email(useremail)
        return user_or_none

    async def start(self) -> None:
        if self.state is SystemState.running:
            return

        await bootstrap(self._user_repo.aioengine)
        await self.system.start(
            eventstore=EventStore(aioengine=self._user_repo.aioengine),
        )
        logger.info("System started")
        self.state = self.state.start()

    async def stop(self):
        await self.system.stop()
        self.state = self.state.stop()

    @asynccontextmanager
    async def setup_system(self):
        try:
            await self.start()
            yield self
        except KeyboardInterrupt:
            logger.info("Quit by user")
        finally:
            await self.stop()

    @classmethod
    def build(cls, settings: Settings) -> ty.Self:
        engine = async_engine_factory(
            settings.db.ASYNC_DB_URL,
            echo=settings.db.ENGINE_ECHO,
            isolation_level=settings.db.ISOLATION_LEVEL,
            pool_pre_ping=True,
        )
        system = GPTSystem(settings=settings, mailbox=MailBox.build())  # type: ignore
        user_repo = repository.UserRepository(aioengine=engine)
        session_repo = repository.SessionRepository(aioengine=engine)
        service = cls(system=system, user_repo=user_repo, session_repo=session_repo)
        return service
