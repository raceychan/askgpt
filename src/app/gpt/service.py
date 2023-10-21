import typing as ty

import openai

from src.app.actor import Actor, ActorRef, System
from src.app.gpt.user import (
    ChatMessage,
    ChatMessageSent,
    ChatSession,
    CompletionModels,
    CreateSession,
    CreateUser,
    SendChatMessage,
    SessionCreated,
    User,
    UserCreated,
)
from src.app.utils.fmtutils import fprint
from src.domain.config import Settings
from src.domain.model import Command, Event, Message
from src.infra.mq import MailBox

"""
            SystemActor
            /
    #     ChatBotActor
    #     /
    # UserActor
    # /
SessionActor
"""


class CompletionOptions(ty.TypedDict, total=False):
    model: str
    message: list
    functions: list
    function_call: str
    temperature: float
    top_p: float
    n: int
    stream: bool
    stop: str | list | None
    max_tokens: int
    presence_penalty: float
    frequency_penalty: float
    logit_bias: dict
    user: str


class OpenAIClient:  # TODO: this might be an (Actor):
    def __init__(self, api_key: str):
        self.__api_key = api_key
        self.client = openai.ChatCompletion
        self.messages = list()

    def send(
        self,
        message: ChatMessage,
        model: CompletionModels,
        stream: bool = True,
        **kwargs: CompletionOptions,
    ):
        self.messages.append(message.asdict())
        resp = self.client.create(
            api_key=self.__api_key,
            messages=self.messages,
            model=model,
            stream=stream,
            **kwargs,
        )
        return resp

    @classmethod
    def from_config(cls, config: Settings):
        return cls(api_key=config.OPENAI_API_KEY)


class SessionActor(Actor):
    entity: ChatSession

    def __init__(self, chat_session: ChatSession):  # , model_client: OpenAIClient):
        super().__init__(mailbox=MailBox.build())
        self.entity = chat_session
        self.model_client: OpenAIClient = OpenAIClient.from_config(
            Settings.from_file("settings.toml")
        )

    def send(self, message: ChatMessage, model: CompletionModels, stream=True):
        chunks = self.model_client.send(message=message, model=model, stream=stream)

        for resp in chunks:
            for choice in resp.choices:  # type: ignore
                content = choice.get("delta", {}).get("content")
                yield content

    def display_message(self, answer: ty.Generator) -> str:
        str_container = ""
        for chunk in answer:
            if chunk is None:
                fprint("\n")
            else:
                fprint(chunk)
                str_container += chunk
        return str_container

    def handle(self, message: Message):
        if type(message) is SendChatMessage:
            chunks = self.send(message=message.chat_message, model=message.model)
            event = ChatMessageSent(
                entity_id=self.entity.user_id,
                session_id=self.entity.session_id,
                chat_message=message.chat_message,
            )
            self.publish(event)
            answer = self.display_message(chunks)

    @classmethod
    def from_event(cls, event: SessionCreated):
        # TODO: this should simply be apply
        return cls(chat_session=ChatSession.apply(event))


class UserActor(Actor):
    entity: User
    childs: dict[ActorRef, SessionActor]

    def __init__(self, user: User):
        super().__init__(mailbox=MailBox.build())
        self.entity = user

    def create_session(self, event: SessionCreated):
        session_actor = SessionActor.from_event(event)
        self.childs[session_actor.entity.entity_id] = session_actor
        self.publish(event)
        return session_actor

    def get_session(self, session_id: str, user_id) -> SessionActor:
        if (session_actor := self.childs.get(session_id, None)) is None:
            event = SessionCreated(session_id=session_id, user_id=user_id)
            session_actor = self.create_session(event)
        return session_actor

    # async def ask_question(self, question: str, session_id: str):
    #     cmd = SendChatMessage(
    #         entity_id=self.entity.entity_id,
    #         session_id=session_id,
    #         user_message=question,
    #     )
    #     await self.handle(cmd)

    @Actor.handle.register
    async def handle(self, command: Command):
        if type(command) is SendChatMessage:
            session = self.get_session(
                session_id=command.session_id, user_id=self.entity.entity_id
            )
            session.handle(command)

    @Actor.handle.register
    async def _(self, command: CreateSession):
        session = self.get_session(
            session_id=command.session_id, user_id=command.user_id
        )

    @classmethod
    def from_event(cls, event: UserCreated):
        return cls(user=User.apply(event))


class GPTSystem(System):
    childs: dict[ActorRef, UserActor]

    def __init__(self):
        super().__init__(mailbox=MailBox.build())

    @System.handle.register
    async def _(self, command: CreateUser):
        self.create(command)

    def create(self, command: CreateUser):
        event = UserCreated(user_id=command.entity_id)
        user_actor = UserActor.from_event(event)
        self.childs[user_actor.entity.entity_id] = user_actor
        self.publish(event)
