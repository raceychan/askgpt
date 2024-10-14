import pytest

from askgpt.app.api.routers.gpt import ChatCompletionRequest


@pytest.fixture
def req():
    return ChatCompletionRequest(
        question="Hello, world!",
    )


def test_chat_completion_request(req: ChatCompletionRequest):
    req = ChatCompletionRequest(
        question="Hello, world!",
    )
    assert req.model == "gpt-3.5-turbo"
    assert req.role == "user"


def test_chat_completion_request_model_dump(req: ChatCompletionRequest):
    req = ChatCompletionRequest(
        question="Hello, world!",
    )
    assert req.model == "gpt-3.5-turbo"
    assert req.role == "user"

    data = req.model_dump(exclude_none=True)
    assert data["question"] == "Hello, world!"
