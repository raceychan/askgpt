import pytest

from askgpt.app.gpt._model import (
    ChatMessage,
    ChatMessageSent,
    ChatResponseReceived,
    ChatSession,
    SessionCreated,
)
from tests.conftest import dft


@pytest.fixture(scope="module")
def chat_message():
    return ChatMessage(role="user", content="ping")


@pytest.fixture(scope="module")
def session_created():
    return SessionCreated(
        session_id=dft.SESSION_ID,
        user_id=dft.USER_ID,
        session_name="New Session",
    )


@pytest.fixture(scope="module")
def chat_message_sent(chat_message: ChatMessage):
    return ChatMessageSent(
        session_id=dft.SESSION_ID,
        chat_message=chat_message,
    )


@pytest.fixture(scope="module")
def chat_response_received():
    return ChatResponseReceived(
        session_id=dft.SESSION_ID,
        chat_message=ChatMessage(role="system", content="pong"),
    )


@pytest.fixture(scope="function")
def chatsession(session_created: SessionCreated):
    return ChatSession.apply(session_created)


@pytest.fixture(scope="module")
def chat_messages():
    return [
        ChatMessage.as_prompt(content="answer me seriously!"),
        ChatMessage.as_user(content="ping"),
        ChatMessage.as_assistant(content="pong"),
        ChatMessage.as_user(content="ask"),
        ChatMessage.as_assistant(content="answer"),
    ]


def test_rebuild_session_by_events(
    chatsession: ChatSession, chat_message_sent: ChatMessageSent
):
    chatsession.apply(chat_message_sent)
    assert chatsession.messages == [chat_message_sent.chat_message]


def test_session_add_message(
    chatsession: ChatSession, chat_messages: list[ChatMessage]
):
    for msg in chat_messages:
        chatsession.add_message(msg)
    assert chatsession.messages == chat_messages
    assert chatsession.prompt == chat_messages[0]
    assert chatsession.prompt and chatsession.prompt.is_prompt
