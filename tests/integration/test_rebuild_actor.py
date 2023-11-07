import typing as ty

import pytest

from src.app.gpt import model, service
from src.domain import config


@pytest.fixture(scope="module")
def chat_messages():
    return [
        model.ChatMessage.as_prompt("answer me seriously!"),
        model.ChatMessage.as_user("ping"),
        model.ChatMessage.as_assistant("pong"),
        model.ChatMessage.as_user("ask"),
        model.ChatMessage.as_assistant("answer"),
    ]


@pytest.fixture(scope="module")
async def gpt_system(settings: config.Settings, eventstore: service.EventStore):
    system = await service.GPTSystem.create(settings, eventstore=eventstore)
    return system


# @pytest.fixture(scope="module")
# def create_user():
#     return model.CreateUser(user_id=model.TestDefaults.USER_ID)


# @pytest.fixture(scope="module")
# def create_session():
#     return model.CreateSession(
#         user_id=model.TestDefaults.USER_ID, session_id=model.TestDefaults.SESSION_ID
#     )


@pytest.fixture(scope="module")
async def user_actor(gpt_system: service.GPTSystem):
    cmd = model.CreateUser(user_id=model.TestDefaults.USER_ID)
    user = await gpt_system.create_child(cmd)
    return user


@pytest.fixture(scope="module")
def openai_client():
    resp = service.ChatResponse(choices=[dict(delta=dict(content="pong"))])

    async def wrapper():
        yield resp

    class FakeClient(service.OpenAIClient):
        async def send_chat(
            self, messages, model, stream: bool = True, **kwargs  # type: ignore
        ) -> ty.AsyncGenerator[service.ChatResponse, None]:
            return wrapper()

    return FakeClient(api_key="fake_key")


@pytest.fixture(scope="function")
async def session_actor(
    user_actor: service.UserActor, openai_client: service.OpenAIClient
):
    cmd = model.CreateSession(
        session_id=model.TestDefaults.SESSION_ID, user_id=model.TestDefaults.USER_ID
    )
    session = await user_actor.create_child(cmd)
    session.set_model_client(openai_client)
    return session


def command_factory(chat_message: model.ChatMessage):
    return model.SendChatMessage(
        session_id=model.TestDefaults.SESSION_ID,
        user_id=model.TestDefaults.USER_ID,
        message_body=chat_message.content,
        role=chat_message.role,
    )


async def test_ask_question(
    session_actor: service.SessionActor, chat_messages: list[model.ChatMessage]
):
    prompt = chat_messages[0]
    cmd = command_factory(prompt)
    await session_actor.receive(cmd)
    journal: service.Journal = session_actor.system.journal  # type: ignore
    events = await journal.eventstore.get(session_actor.entity_id)

    assert events[0].__class__ is model.SessionCreated
    assert events[1].__class__ is model.ChatMessageSent
    assert events[2].__class__ is model.ChatResponseReceived


async def test_session_self_rebuild(gpt_system: service.GPTSystem):
    events = await gpt_system.journal.eventstore.get(model.TestDefaults.SESSION_ID)
    session_actor = service.SessionActor.rebuild(events)
    assert isinstance(session_actor, service.SessionActor)
    assert session_actor.entity_id == model.TestDefaults.SESSION_ID
    assert session_actor.entity.messages[0] == events[0].chat_message
    assert session_actor.entity.messages[1] == events[1].chat_message


async def test_user_self_rebuild():
    ...


async def test_user_rebuild_session():
    ...
