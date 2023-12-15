import pytest

from src import cli
from src.app.gpt import service
from src.domain.config import Settings
from src.domain.model.test_default import TestDefaults


@pytest.fixture(scope="module")
def gpt_options():
    return cli.CLIOptions(
        command="gpt",
        question="ping",
        username=TestDefaults.USER_NAME,
        email=TestDefaults.USER_EMAIL,
        password=TestDefaults.USER_PASSWORD,
        session_id=TestDefaults.SESSION_ID,
    )


@pytest.fixture(scope="module")
def auth_options():
    return cli.CLIOptions(
        command="auth",
        username=TestDefaults.USER_NAME,
        email=TestDefaults.USER_EMAIL,
        password=TestDefaults.USER_PASSWORD,
    )


@pytest.fixture(scope="module")
async def gpt(settings: Settings):
    gpt_service = service.GPTService.from_settings(settings)
    async with gpt_service.lifespan() as gpt:
        yield gpt


@pytest.mark.skip(reason="io involved")
async def test_create_user(gpt: service.GPTService, auth_options: cli.CLIOptions):
    await cli.app(gpt, auth_options)


@pytest.mark.skip(reason="io involved")
async def test_cli_app(gpt: service.GPTService, gpt_options: cli.CLIOptions):
    await cli.app(gpt, gpt_options)
