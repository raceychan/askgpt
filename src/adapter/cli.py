import asyncio
from argparse import ArgumentParser, Namespace

from src.app import gpt
from src.domain import Settings


class CLIOptions(Namespace):
    question: str | None
    user_id: str = gpt.model.TestDefaults.USER_ID
    session_id: str = gpt.model.TestDefaults.SESSION_ID
    model: str = gpt.model.TestDefaults.MODEL
    interactive: bool = False

    def validate(self) -> None:
        models = gpt.model.CompletionModels.__args__  # type: ignore
        if self.model not in models:
            raise ValueError(f"model must be one of {models}")

        if self.question and self.interactive:
            raise ValueError("question and interactive are mutually exclusive")


def cli() -> CLIOptions:
    parser = ArgumentParser(description="gpt client in zen mode")
    parser.add_argument("question", type=str, nargs="?")
    parser.add_argument("--user_id", type=str, nargs="?")
    parser.add_argument("--session_id", type=str, nargs="?")
    parser.add_argument("--model", type=str, nargs="?")
    parser.add_argument("-i", "--interactive", action="store_true")
    namespace: CLIOptions = parser.parse_args(namespace=CLIOptions())  # type: ignore
    namespace.validate()
    return namespace


# async def rebuild_system(engine):
#     raise NotImplementedError
#     from src.infra.eventstore import EventStore

#     eventstore: EventStore = EventStore(engine)

#     ...


async def send_question(question: str, system: gpt.service.GPTSystem) -> None:
    command = gpt.model.SendChatMessage(
        user_id=gpt.model.TestDefaults.USER_ID,
        session_id=gpt.model.TestDefaults.SESSION_ID,
        message_body=question,
        role="user",
    )

    await system.receive(command)


async def interactive(system: gpt.service.GPTSystem) -> None:
    while True:
        question = input("\nwhat woud you like to ask?\n\n")
        await send_question(question, system)


async def app(options: CLIOptions) -> None:
    # TODO: make this a method of system
    # async with gpt.service.set_upsytem(settings) as system:
    #     if options.question:
    #         await system.send_question(options.question)
    #     else:
    #         await system.interactive()

    settings = Settings.from_file("settings.toml")

    system = await gpt.service.setup_system(settings)

    try:
        await service_dispatch(options, system)
    except KeyboardInterrupt:
        quit("\nBye")
    finally:
        await system.stop()


async def service_dispatch(options: CLIOptions, system: gpt.service.GPTSystem) -> None:
    if options.question:
        await send_question(options.question, system)
    elif options.interactive:
        await interactive(system)


if __name__ == "__main__":
    namespace = cli()
    asyncio.run(app(namespace))
