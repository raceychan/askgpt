import typing as ty
from argparse import ArgumentParser

from src.app.service import event_listener, gpt
from src.domain.config import Settings


def cli():
    parser = ArgumentParser(prog=settings.PROJECT_NAME)
    parser.add_argument("--show", action="store_true")
    parser.add_argument("--message")
    parser.add_argument("--model")

    namespace = parser.parse_args()

    app(namespace)


def app(namespace):
    settings = Settings.from_file()
    system = gpt.System(model_client=gpt.OpenAIClient.from_config(settings))
    user = gpt.User.apply(gpt.UserCredated(user_id="admin"))
    system.add_user(user)

    cmd = gpt.SendChatMessage(user_message="what is your name?")
    system.handle(cmd)
