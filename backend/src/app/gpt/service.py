import typing as ty
from contextlib import asynccontextmanager

from src.app.actor import QueueBox as QueueBox
from src.app.auth import repository as auth_repo
from src.app.gpt import gptclient, model, params
from src.app.gpt import repository as gpt_repo
from src.app.gpt.gptsystem import GPTSystem, SessionActor, SystemState, UserActor
from src.domain._log import logger
from src.domain.base import SupportedGPTs
from src.infra import eventstore, security


class GPTService:
    def __init__(
        self,
        system: GPTSystem,
        encryptor: security.Encrypt,
        user_repo: auth_repo.UserRepository,
        session_repo: gpt_repo.SessionRepository,
    ):
        self._service_state = SystemState.created
        self._system = system
        self._encryptor = encryptor
        self._user_repo = user_repo
        self._session_repo = session_repo
        self._client_registry = gptclient.ClientRegistry()

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

    async def build_api_pool(self, user_id: str, api_type: str):
        encrypted_api_keys = await self._user_repo.get_api_keys_for_user(
            user_id=user_id, api_type=api_type
        )
        if not encrypted_api_keys:
            raise Exception("no api keys found for user")

        api_keys = tuple(
            self._encryptor.decrypt_string(key) for key in encrypted_api_keys
        )

        pool_keyspace = self.system.settings.redis.keyspaces.API_POOL / user_id
        user_api_pool = gptclient.APIPool(
            pool_keyspace=pool_keyspace,
            api_type=api_type,
            api_keys=api_keys,
            cache=self.system.cache,
        )
        return user_api_pool

    async def stream_chat(
        self,
        user_id: str,
        session_id: str,
        gpt_type: SupportedGPTs,
        role: params.ChatGPTRoles,
        question: str,
        options: dict[str, ty.Any],
    ) -> ty.AsyncGenerator[str | None, None]:
        api_pool = await self.build_api_pool(user_id=user_id, api_type=gpt_type)
        async with api_pool.lifespan():
            async with api_pool.reserve_api_key() as api_key:
                client_factory = self._client_registry[gpt_type]
                client = client_factory.from_apikey(api_key)
                session_actor = await self.get_session(
                    user_id=user_id, session_id=session_id
                )
                completion_model = options.pop("model")
                ans_gen = session_actor.send_chatmessage(
                    client=client,
                    message=model.ChatMessage(role=role, content=question),
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
            eventstore=eventstore.EventStore(aiodb=self._session_repo.aiodb),
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
