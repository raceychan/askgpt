# import pytest

# from src.cli import CLIOptions, InvalidOption
# from src.domain.model.test_default import TestDefaults


# def test_validate(test_defaults: TestDefaults):
#     options = CLIOptions(
#         question="hello",
#         user_id=test_defaults.USER_ID,
#         session_id=test_defaults.SESSION_ID,
#         model="gpt-3.5-turbo",
#         interactive=False,
#     )
#     options.validate()
#     assert options.user_id == test_defaults.USER_ID
#     assert options.session_id == test_defaults.SESSION_ID
#     assert options.interactive is False


# def test_validate_fail():
#     options = CLIOptions(question="hello", interactive=True)
#     with pytest.raises(InvalidOption):
#         options.validate()


# async def test_question():
#     options = CLIOptions(question="hello", interactive=False)
#     assert options.question == "hello"
