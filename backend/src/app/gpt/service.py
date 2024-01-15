import typing as ty
from contextlib import asynccontextmanager

from src.app.actor import QueueBox as QueueBox
from src.app.gpt import errors, model, params, repository
from src.app.gpt.gptsystem import GPTSystem, SessionActor, SystemState, UserActor
from src.domain._log import logger
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

    async def check_corresponding_api_provided(
        self, user_id: str, api_type: str
    ) -> None:
        user = await self.get_user(user_id=user_id)
        keys = user.entity.get_keys_of_type(api_type)
        if not keys:
            raise errors.APIKeyNotProvidedError(user_id=user_id, api_type=api_type)

    async def stream_chat(
        self,
        user_id: str,
        session_id: str,
        gpt_type: str,
        role: params.ChatGPTRoles,
        question: str,
        options: dict[str, ty.Any],
    ) -> ty.AsyncGenerator[str | None, None]:
        session_actor = await self.get_session(user_id=user_id, session_id=session_id)
        completion_model = options.pop("model")
        ans_gen = session_actor.send_chatmessage(
            message=model.ChatMessage(role=role, content=question),
            model_type=gpt_type,
            completion_model=completion_model,
            options=options,
        )
        return ans_gen

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
            eventstore=EventStore(aiodb=self._session_repo.aiodb),
        )
        self.state = self.state.start()
        logger.success("gpt service started")

    async def stop(self):
        await self.system.stop()
        self.state = self.state.stop()

    @asynccontextmanager
    async def lifespan(self):
        await self.start()
        try:
            yield self
        finally:
            await self.stop()
