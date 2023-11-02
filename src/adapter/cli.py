import asyncio
from argparse import ArgumentParser, Namespace

from src.app import gpt
from src.domain.config import Settings


class CLIOptions(Namespace):
    question: str | None
    user_id: str = gpt.model.TestDefaults.USER_ID
    session_id: str = gpt.model.TestDefaults.SESSION_ID
    model: str = gpt.model.TestDefaults.MODEL
    interactive: bool = False

    def validate(self):
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
    namespace: CLIOptions = parser.parse_args(namespace=CLIOptions())
    namespace.validate()
    return namespace


async def setup_system(settings: Settings):
    eventstore = gpt.service.EventStore.build(db_url=settings.db.ASYNC_DB_URL)
    system_started = gpt.service.SystemStarted(entity_id="system", settings=settings)
    system: gpt.service.GPTSystem = gpt.service.GPTSystem.apply(system_started)
    system.create_eventlog()
    system.create_journal(eventstore=eventstore, mailbox=gpt.service.MailBox.build())
    # system = await gpt.service.GPTSystem.create(settings)
    return system


async def rebuild_system(engine):
    from src.infra.eventstore import EventStore

    eventstore: EventStore = EventStore(engine)

    ...


async def send_question(question: str, system: gpt.service.GPTSystem):
    command = gpt.model.SendChatMessage(
        user_id=gpt.model.TestDefaults.USER_ID,
        session_id=gpt.model.TestDefaults.SESSION_ID,
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


if __name__ == "__main__":
    namespace = cli()
    asyncio.run(app(namespace))
