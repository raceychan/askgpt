import pytest
from askgpt.app.gpt.openai._params import OpenAIChatMessageOptions


@pytest.fixture
def req():
    return OpenAIChatMessageOptions(
        message={"role": "user", "content": "Hello, world!"},
        model="gpt-3.5-turbo",
    )


def test_chat_completion_request_model_dump(req: OpenAIChatMessageOptions):
    assert req["model"] == "gpt-3.5-turbo"
    assert req["message"]["role"] == "user"
    assert req["message"]["content"] == "Hello, world!"
