import asyncio
from argparse import ArgumentParser, Namespace

from src.app.gpt import model, service
from src.domain.config import Settings


class CLIOptions(Namespace):
    question: str | None
    user_id: str = model.TestDefaults.USER_ID
    session_id: str = model.TestDefaults.SESSION_ID
    model: str = model.TestDefaults.MODEL
    interactive: bool = False

    def validate(self) -> None:
        # BUG: loses all default values
        models = model.CompletionModels.__args__  # type: ignore
        if self.model not in models:
            raise ValueError(f"model must be one of {models}, received: {self.model}")

        if self.question and self.interactive:
            raise ValueError("question and interactive are mutually exclusive")
        elif not self.question and not self.interactive:
            raise ValueError("question or interactive is required")

    @classmethod
    def parse(cls):
        parser = ArgumentParser(description="gpt client in zen mode")
        sub = parser.add_subparsers(required=True)

        gpt = sub.add_parser("gpt", help="gpt client")
        gpt.add_argument("question", type=str, nargs="?")
        gpt.add_argument(
            "--user_id", default=model.TestDefaults.USER_ID, type=str, nargs="?"
        )
        gpt.add_argument(
            "--session_id", default=model.TestDefaults.SESSION_ID, type=str, nargs="?"
        )
        gpt.add_argument(
            "--model", default=model.TestDefaults.MODEL, type=str, nargs="?"
        )
        gpt.add_argument("-i", "--interactive", action="store_true")

        auth = sub.add_parser("auth", help="gpt auth client")
        auth.add_argument("--user_name", type=str, nargs="?")
        auth.add_argument("--email", type=str, nargs="?")
        auth.add_argument("--password", type=str, nargs="?")

        namespace = parser.parse_args(namespace=CLIOptions())
        namespace.validate()
        return namespace


async def service_dispatch(gptservice: service.GPTService, options: CLIOptions) -> None:
    async with gptservice.setup_system() as gpt:
        if options.question:
            await gpt.send_question(options.question)
        elif options.interactive:
            await gpt.interactive()


async def app(options: CLIOptions, settings: Settings) -> None:
    gpt = service.GPTService(settings)
    async with gpt.setup_system() as system:
        await service_dispatch(system, options)


def main():
    options = CLIOptions.parse()
    settings = Settings.from_file("settings.toml")
    asyncio.run(app(options, settings))


if __name__ == "__main__":
    main()
