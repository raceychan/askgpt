import pytest

from src.app.model import TestDefaults
from src.cli import CLIOptions, InvalidOption


def test_validate(test_defaults: TestDefaults):
    options = CLIOptions(question="hello", interactive=False)
    options.validate()
    assert options.user_id == test_defaults.USER_ID
    assert options.session_id == test_defaults.SESSION_ID
    assert options.interactive is False


def test_validate_fail():
    options = CLIOptions(question="hello", interactive=True)
    with pytest.raises(InvalidOption):
        options.validate()


async def test_question():
    options = CLIOptions(question="hello", interactive=False)
    assert options.question == "hello"
