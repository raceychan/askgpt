import typing as ty
from contextlib import asynccontextmanager

from src.app.actor import QueueBox
from src.app.gpt import model, repository
from src.app.gpt.gptsystem import GPTSystem, SessionActor, SystemState, UserActor
from src.domain._log import logger
from src.domain.config import Settings
from src.infra import factory
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

    async def send_question(
        self,
        user_id: str,
        session_id: str,
        question: str,
        role: model.ChatGPTRoles,
        completion_model: model.CompletionModels,
    ) -> None:
        session_actor = await self.get_session(user_id=user_id, session_id=session_id)

        command = model.SendChatMessage(
            user_id=user_id,
            session_id=session_id,
            message_body=question,
            role=role,
            model=completion_model,
        )

        await session_actor.receive(command)

    async def stream_chat(
        self,
        user_id: str,
        session_id: str,
        question: str,
        role: model.ChatGPTRoles,
        completion_model: model.CompletionModels,
    ) -> ty.AsyncGenerator[str | None, None]:
        session_actor = await self.get_session(user_id=user_id, session_id=session_id)
        return session_actor.send_chatmessage(
            message=model.ChatMessage(role=role, content=question),
            completion_model=completion_model,
        )

    async def interactive(
        self, user_id: str, session_id: str, completion_model: model.CompletionModels
    ) -> None:
        while True:
            question = input("\nwhat woud you like to ask?\n\n")
            await self.send_question(
                user_id,
                session_id,
                question,
                role="user",
                completion_model=completion_model,
            )

    async def create_session(self, user_id: str) -> str:
        user_actor = self.system.get_child(user_id)
        if not user_actor:
            user_actor = await self.system.rebuild_user(user_id)

        session_id = model.uuid_factory()
        await user_actor.handle(
            model.CreateSession(user_id=user_id, session_id=session_id)
        )
        return session_id

    async def get_user(self, user_id: str) -> UserActor:
        user_actor = self.system.get_child(user_id)
        if user_actor is None:
            user_actor = await self.system.rebuild_user(user_id)
        return user_actor

    async def get_session(self, user_id: str, session_id: str) -> SessionActor:
        user_actor = await self.get_user(user_id)
        session_actor = user_actor.get_child(session_id)
        if session_actor is None:
            session_actor = await user_actor.rebuild_session(session_id)
        return session_actor



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
    def from_settings(cls, settings: Settings) -> ty.Self:
        aioengine = factory.get_async_engine(settings)
        system = GPTSystem(
            settings=settings,
            ref=settings.actor_refs.SYSTEM,
            boxfactory=QueueBox,
            cache=factory.get_cache(settings),
        )
        session_repo = repository.SessionRepository(aioengine)
        service = cls(system=system, session_repo=session_repo)
        return service
