import asyncio
import typing as ty
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass

from src.app.factory import AuthService, get_auth_service
from src.app.gpt import model, params, service
from src.domain._log import logger
from src.domain.base import EMPTY_STR
from src.domain.config import get_setting


class InvalidOption(Exception):
    ...


@dataclass
class CLIOptions(Namespace):
    username: str = EMPTY_STR
    email: str = EMPTY_STR
    password: str = EMPTY_STR
    question: str = EMPTY_STR
    user_id: str = EMPTY_STR
    session_id: str = EMPTY_STR
    model: params.CompletionModels = "gpt-3.5-turbo"
    interactive: bool = False
    command: ty.Literal["gpt", "auth"] = "gpt"

    def validate(self) -> None:
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
        gpt.add_argument("--user_id", type=str, nargs="?")
        gpt.add_argument("--session_id", type=str, nargs="?")
        gpt.add_argument("--model", type=str, nargs="?")
        gpt.add_argument("-i", "--interactive", action="store_true")

        auth = sub.add_parser("auth", help="gpt auth client")
        auth.add_argument("--username", type=str, nargs="?")
        auth.add_argument("--email", type=str, nargs="?")
        auth.add_argument("--password", type=str, nargs="?")

        args = parser.parse_args(namespace=CLIOptions())
        args.validate()
        return args


async def gpt_dispatch(gpt: service.GPTService, options: CLIOptions) -> None:
    if options.question:
        await gpt.send_question(
            user_id=options.user_id,
            session_id=options.session_id,
            question=options.question,
            role="user",
            completion_model=options.model,
        )
    elif options.interactive:
        await gpt.interactive(
            user_id=options.user_id,
            session_id=options.session_id,
            completion_model=options.model,
        )


async def auth_dispatch(auth: AuthService, options: CLIOptions):
    # TODO: use email as user id
    username = options.username
    email = options.email
    password = options.password

    user = await auth.find_user(useremail=email)

    if not user:
        await auth.signup_user(username, email, password)
    else:
        logger.info(
            f"User: {user.user_info.user_email} already exists, user id: {user.entity_id}"
        )


async def app(gpt: service.GPTService, options: CLIOptions) -> None:
    async with gpt.lifespan() as system:
        await gpt_dispatch(system, options)


def main():
    options = CLIOptions.parse()
    settings = get_setting()
    gpt = service.GPTService.from_settings(settings)
    auth = get_auth_service(settings)

    if options.command == "auth":
        asyncio.run(auth_dispatch(auth, options))
    elif options.command == "gpt":
        asyncio.run(app(gpt, options))


if __name__ == "__main__":
    raise NotImplementedError(
        "Cli needs re-implementation and is currently disabled due to the complexity of apis"
    )
    # main()
