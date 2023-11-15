import asyncio

# from src.app import gpt
from argparse import ArgumentParser, Namespace

from src.app.gpt import model, service
from src.domain._log import logger
from src.domain.config import Settings


class CLIOptions(Namespace):
    question: str | None
    user_id: str = model.TestDefaults.USER_ID
    session_id: str = model.TestDefaults.SESSION_ID
    model: str = model.TestDefaults.MODEL
    interactive: bool = False

    def validate(self) -> None:
        models = model.CompletionModels.__args__  # type: ignore
        if self.model not in models:
            raise ValueError(f"model must be one of {models}")

        if self.question and self.interactive:
            raise ValueError("question and interactive are mutually exclusive")

    @classmethod
    def parse(cls):
        parser = ArgumentParser(description="gpt client in zen mode")
        parser.add_argument("question", type=str, nargs="?")
        parser.add_argument("--user_id", type=str, nargs="?")
        parser.add_argument("--session_id", type=str, nargs="?")
        parser.add_argument("--model", type=str, nargs="?")
        parser.add_argument("-i", "--interactive", action="store_true")
        namespace: CLIOptions = parser.parse_args(namespace=CLIOptions())
        namespace.validate()
        return namespace


# async def rebuild_system(engine):
#     raise NotImplementedError
#     from src.infra.eventstore import EventStore

#     eventstore: EventStore = EventStore(engine)

#     ...


async def send_question(question: str, system: service.GPTSystem) -> None:
    command = model.SendChatMessage(
        user_id=model.TestDefaults.USER_ID,
        session_id=model.TestDefaults.SESSION_ID,
        message_body=question,
        role="user",
    )

    await system.receive(command)


async def interactive(system: service.GPTSystem) -> None:
    while True:
        question = input("\nwhat woud you like to ask?\n\n")
        await send_question(question, system)


async def app(options: CLIOptions, settings: Settings) -> None:
    async with service.setup_system(settings) as system:
        logger.info("system started")
        await service_dispatch(options, system)


async def service_dispatch(options: CLIOptions, system: service.GPTSystem) -> None:
    if options.question:
        await send_question(options.question, system)
    elif options.interactive:
        await interactive(system)


if __name__ == "__main__":
    namespace = CLIOptions.parse()
    settings = Settings.from_file("settings.toml")
    asyncio.run(app(namespace, settings))
