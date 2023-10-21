import asyncio
from argparse import ArgumentParser, Namespace

from src.app import Mediator, gpt, journal
from src.domain.config import Settings, TestDefaults

settings = Settings.from_file("settings.toml")


def setup_system(settings: Settings):
    system = gpt.service.GPTSystem()
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


# async def record_event():
#     recorder = journal.setup_journal(settings)
#     await recorder.start()


async def send_question(question: str, mediator: Mediator):
    command = gpt.service.SendChatMessage(
        entity_id=TestDefaults.user_id,
        session_id=TestDefaults.session_id,
        user_message=question,
    )
    await mediator.send(command)


async def interactive(mediator: Mediator):
    while True:
        question = input("what woud you like to ask?")
        command = gpt.service.SendChatMessage(
            entity_id=TestDefaults.user_id,
            session_id=TestDefaults.session_id,
            user_message=question,
        )
        await mediator.send(command)


async def app(options: CLIOptions):
    system = gpt.service.setup_system(settings)
    mediator = Mediator()
    mediator.__class__.register(gpt.service.Command, system)
    asyncio.create_task(record_event())

    if options.question:
        await send_question(options.question, mediator)
    elif options.interactive:
        await interactive(mediator)


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
