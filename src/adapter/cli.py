import asyncio
import typing as ty
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass

from src.app.gpt import model, service
from src.domain.config import Settings


class InvalidOption(Exception):
    ...


@dataclass
class CLIOptions(Namespace):
    username: str = ""
    email: str = ""
    password: str = ""
    question: str = ""
    user_id: str = model.TestDefaults.USER_ID
    session_id: str = model.TestDefaults.SESSION_ID
    model: str = model.TestDefaults.MODEL
    interactive: bool = False
    command: ty.Literal["gpt", "auth"] = "gpt"

    def validate(self) -> None:
        # BUG: loses all default values
        if self.command == "gpt":
            models = model.CompletionModels.__args__  # type: ignore
            if self.model not in models:
                raise InvalidOption(
                    f"model must be one of {models}, received: {self.model}"
                )
            if self.question and self.interactive:
                raise InvalidOption("question and interactive are mutually exclusive")
            elif not self.question and not self.interactive:
                raise InvalidOption("question or interactive is required")
        elif self.command == "auth":
            if not self.email:
                raise InvalidOption("email is required")
            if not self.password:
                raise InvalidOption("password is required")
            if not self.username:
                self.username = self.email.split("@")[0]
        else:
            raise NotImplementedError(f"command {self.command} not implemented")

    @classmethod
    def parse(cls):
        parser = ArgumentParser(description="gpt client in zen mode")
        sub = parser.add_subparsers(dest="command", required=True)

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
        auth.add_argument("--username", type=str, nargs="?")
        auth.add_argument("--email", type=str, nargs="?")
        auth.add_argument("--password", type=str, nargs="?")

        args = parser.parse_args(namespace=CLIOptions())
        args.validate()
        return args


async def gpt_dispatch(gpt: service.GPTService, options: CLIOptions) -> None:
    await gpt.login(options.email, options.password)
    if options.question:
        await gpt.send_question(options.question)
    elif options.interactive:
        await gpt.interactive()


async def auth_dispatch(gptservice: service.GPTService, options: CLIOptions):
    username = options.username
    email = options.email
    password = options.password

    user = await gptservice.find_user(username=username, useremail=email)
    if not user:
        await gptservice.create_user(username, email, password)


async def app(gpt: service.GPTService, options: CLIOptions) -> None:
    async with gpt.setup_system() as system:
        if options.command == "auth":
            await auth_dispatch(system, options)
        elif options.command == "gpt":
            await gpt_dispatch(system, options)


def main():
    options = CLIOptions.parse()
    settings = Settings.from_file("settings.toml")
    gpt = service.GPTService.build(settings)
    asyncio.run(app(gpt, options))


if __name__ == "__main__":
    main()
