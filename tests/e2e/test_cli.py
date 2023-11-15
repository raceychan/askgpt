import pytest

from src.adapter import cli
from src.domain.config import Settings


@pytest.fixture(scope="module")
def cli_options():
    return cli.CLIOptions(question="ping")


@pytest.mark.skip("debugging")
async def test_cli_app(cli_options: cli.CLIOptions, settings: Settings):
    # NOTE: this would create a new eventstore table
    await cli.app(cli_options, settings)
