import pytest

from src.app.gpt import model
from src.app.model import TestDefaults


@pytest.fixture(scope="module")
def chat_message():
    return model.ChatMessage(role="user", content="ping")


@pytest.fixture(scope="module")
def session_created():
    return model.SessionCreated(
        session_id=TestDefaults.SESSION_ID, user_id=TestDefaults.USER_ID
    )


@pytest.fixture(scope="module")
def chat_message_sent(chat_message: model.ChatMessage):
    return model.ChatMessageSent(
        session_id=TestDefaults.SESSION_ID,
        chat_message=chat_message,
    )


@pytest.fixture(scope="module")
def chat_response_received():
    return model.ChatResponseReceived(
        session_id=TestDefaults.SESSION_ID,
        chat_message=model.ChatMessage(role="system", content="pong"),
    )


@pytest.fixture(scope="function")
def chatsession(session_created: model.SessionCreated):
    return model.ChatSession.apply(session_created)


@pytest.fixture(scope="module")
def chat_messages():
    return [
        model.ChatMessage.as_prompt("answer me seriously!"),
        model.ChatMessage.as_user("ping"),
        model.ChatMessage.as_assistant("pong"),
        model.ChatMessage.as_user("ask"),
        model.ChatMessage.as_assistant("answer"),
    ]


def test_rebuild_session_by_events(
    chatsession: model.ChatSession, chat_message_sent: model.ChatMessageSent
):
    chatsession.apply(chat_message_sent)
    assert chatsession.messages == [chat_message_sent.chat_message]


def test_session_add_message(
    chatsession: model.ChatSession, chat_messages: list[model.ChatMessage]
):
    for msg in chat_messages:
        chatsession.add_message(msg)
    assert chatsession.messages == chat_messages
    assert chatsession.prompt == chat_messages[0]
    assert chatsession.prompt and chatsession.prompt.is_prompt
