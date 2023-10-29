import asyncio
from argparse import ArgumentParser, Namespace

from src.app import gpt
from src.domain.config import Settings, TestDefaults


async def setup_system(settings: Settings):
    system = await gpt.service.GPTSystem.create(settings)
    return system


class CLIOptions(Namespace):
    question: str | None
    user_id: str = TestDefaults.user_id
    session_id: str = TestDefaults.session_id
    model: str = TestDefaults.model
    interactive: bool = False

    def validate(self):
        models = gpt.service.CompletionModels.__args__  # type: ignore
        if self.model not in models:
            raise ValueError(f"model must be one of {models}")

        if self.question and self.interactive:
            raise ValueError("question and interactive are mutually exclusive")


async def send_question(question: str, system: gpt.service.GPTSystem):
    command = gpt.service.SendChatMessage(
        user_id=TestDefaults.user_id,
        session_id=TestDefaults.session_id,
        user_message=question,
    )

    await system.receive(command)


async def interactive(system: gpt.service.GPTSystem):
    while True:
        question = input("\nwhat woud you like to ask?\n\n")
        await send_question(question, system)


async def app(options: CLIOptions):
    settings = Settings.from_file("settings.toml")

    system = await setup_system(settings)

    if options.question:
        await send_question(options.question, system)
    elif options.interactive:
        try:
            await interactive(system)
        except KeyboardInterrupt:
            quit("\nBye")
        finally:
            await system.stop()


def cli() -> CLIOptions:
    parser = ArgumentParser(description="gpt client in zen mode")
    parser.add_argument("question", type=str, nargs="?")
    parser.add_argument("--user_id", type=str, nargs="?")
    parser.add_argument("--session_id", type=str, nargs="?")
    parser.add_argument("--model", type=str, nargs="?")
    parser.add_argument("-i", "--interactive", action="store_true")
    namespace: CLIOptions = parser.parse_args(namespace=CLIOptions())
    namespace.validate()
    return namespace


if __name__ == "__main__":
    namespace = cli()
    asyncio.run(app(namespace))
