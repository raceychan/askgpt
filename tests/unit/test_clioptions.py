import pytest

from src.adapter.cli import CLIOptions, TestDefaults


def test_validate():
    options = CLIOptions(question="hello", interactive=False)
    options.validate()
    assert options.user_id == TestDefaults.user_id
    assert options.session_id == TestDefaults.session_id
    assert options.interactive == False


def test_validate_fail():
    options = CLIOptions(question="hello", interactive=True)
    with pytest.raises(ValueError):
        options.validate()


async def test_question():
    options = CLIOptions(question="hello", interactive=False)
    assert options.question == "hello"
