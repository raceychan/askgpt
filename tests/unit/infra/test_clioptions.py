import pytest

from src.adapter.cli import CLIOptions, gpt


def test_validate():
    options = CLIOptions(question="hello", interactive=False)
    options.validate()
    assert options.user_id == gpt.model.TestDefaults.USER_ID
    assert options.session_id == gpt.model.TestDefaults.SESSION_ID
    assert options.interactive is False


def test_validate_fail():
    options = CLIOptions(question="hello", interactive=True)
    with pytest.raises(ValueError):
        options.validate()


async def test_question():
    options = CLIOptions(question="hello", interactive=False)
    assert options.question == "hello"
