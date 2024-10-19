import pytest

from askgpt.app.gpt._params import CompletionOptions


@pytest.fixture
def req():
    return CompletionOptions(
        message={"role": "user", "content": "Hello, world!"},
        model="gpt-3.5-turbo",
    )


def test_chat_completion_request_model_dump(req: CompletionOptions):
    assert req["model"] == "gpt-3.5-turbo"
    assert req["message"]["role"] == "user"
    assert req["message"]["content"] == "Hello, world!"
