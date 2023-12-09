import typing as ty
from contextlib import asynccontextmanager

from src.app.actor import MailBox
from src.app.gpt import model, repository
from src.app.gpt.system import GPTSystem, SessionActor, SystemState, UserActor
from src.domain._log import logger
from src.domain.config import Settings
from src.infra import encrypt, factory
from src.infra.eventstore import EventStore


class GPTService:
    def __init__(
        self,
        system: GPTSystem,
        session_repo: repository.SessionRepository,
    ):
        self._service_state = SystemState.created
        self._system = system
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

    async def send_question(self, user_id: str, session_id: str, question: str) -> None:
        # TODO: get before rebuild
        user_actor = await self.system.rebuild_user(user_id)
        session_actor = await user_actor.rebuild_session(session_id)

        command = model.SendChatMessage(
            user_id=user_id,
            session_id=session_id,
            message_body=question,
            role="user",
        )

        await session_actor.receive(command)

    async def interactive(self, user_id: str, session_id: str) -> None:
        while True:
            question = input("\nwhat woud you like to ask?\n\n")
            await self.send_question(user_id, session_id, question)

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

    async def create_session(self, user_id: str, session_id: str) -> SessionActor:
        user_actor = self.system.get_child(user_id)
        if not user_actor:
            user_actor = await self.system.rebuild_user(user_id)

        await user_actor.handle(
            model.CreateSession(user_id=user_id, session_id=session_id)
        )
        return user_actor.select_child(session_id)

    async def start(self) -> None:
        if self.state.is_running:
            return

        await self.system.start(
            eventstore=EventStore(aioengine=self._session_repo.aioengine),
        )
        logger.info("System started")
        self.state = self.state.start()

    async def stop(self):
        await self.system.stop()
        self.state = self.state.stop()

    @asynccontextmanager
    async def lifespan(self):
        try:
            await self.start()
            yield self
        except KeyboardInterrupt:
            logger.info("Quit by user")
        finally:
            await self.stop()

    @classmethod
    def build(cls, settings: Settings) -> ty.Self:
        aioengine = factory.get_async_engine(settings)
        system = GPTSystem(
            settings=settings, ref=settings.actor_refs.SYSTEM, mailbox=MailBox.build()
        )
        session_repo = repository.SessionRepository(aioengine)
        service = cls(system=system, session_repo=session_repo)
        return service
