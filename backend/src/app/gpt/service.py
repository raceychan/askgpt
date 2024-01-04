import typing as ty
from contextlib import asynccontextmanager

from src.app.actor import QueueBox as QueueBox
from src.app.gpt import model, params, repository
from src.app.gpt.gptsystem import GPTSystem, SessionActor, SystemState, UserActor
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
        model_type: str,
        role: model.ChatGPTRoles,
        completion_model: model.CompletionModels,
        **options: ty.Unpack[params.CompletionOptions],
    ) -> ty.AsyncGenerator[str | None, None]:
        session_actor = await self.get_session(user_id=user_id, session_id=session_id)
        return session_actor.send_chatmessage(
            message=model.ChatMessage(role=role, content=question),
            model_type=model_type,
            completion_model=completion_model,
            options=options,
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

        if self.system.state is SystemState.running:
            return

        await self.system.start(
            eventstore=EventStore(aioengine=self._session_repo.aioengine),
        )
        self.state = self.state.start()

    async def stop(self):
        await self.system.stop()
        await self._session_repo._aioengine.dispose()
        self.state = self.state.stop()

    @asynccontextmanager
    async def lifespan(self):
        await self.start()
        try:
            yield self
        finally:
            await self.stop()
