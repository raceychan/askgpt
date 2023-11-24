import pytest

from src.adapter.cli import CLIOptions, InvalidOption

# from src.app import gpt
from src.app.gpt import model


def test_validate():
    options = CLIOptions(question="hello", interactive=False)
    options.validate()
    assert options.user_id == model.TestDefaults.USER_ID
    assert options.session_id == model.TestDefaults.SESSION_ID
    assert options.interactive is False


def test_validate_fail():
    options = CLIOptions(question="hello", interactive=True)
    with pytest.raises(InvalidOption):
        options.validate()


async def test_question():
    options = CLIOptions(question="hello", interactive=False)
    assert options.question == "hello"
