import pytest

from src.adapter import cli
from src.app.gpt import model, service
from src.domain.config import Settings


@pytest.fixture(scope="module")
def gpt_options():
    return cli.CLIOptions(
        command="gpt",
        question="ping",
        username=model.TestDefaults.USER_NAME,
        email=model.TestDefaults.USER_EMAIL,
        password=model.TestDefaults.USER_PASSWORD,
        session_id=model.TestDefaults.SESSION_ID,
    )


@pytest.fixture(scope="module")
def auth_options():
    return cli.CLIOptions(
        command="auth",
        username=model.TestDefaults.USER_NAME,
        email=model.TestDefaults.USER_EMAIL,
        password=model.TestDefaults.USER_PASSWORD,
    )


@pytest.fixture(scope="module")
async def gpt(settings: Settings):
    gpt_service = service.GPTService.build(settings)
    async with gpt_service.setup_system() as gpt:
        yield gpt


@pytest.mark.skip(reason="io involved")
async def test_create_user(gpt: service.GPTService, auth_options: cli.CLIOptions):
    await cli.app(gpt, auth_options)


@pytest.mark.skip(reason="io involved")
async def test_cli_app(gpt: service.GPTService, gpt_options: cli.CLIOptions):
    await cli.app(gpt, gpt_options)
