import typing as ty
from argparse import ArgumentParser

from src.app.service import event_listener, gpt
from src.domain.config import Settings


def cli():
    parser = ArgumentParser()  # prog=settings.PROJECT_NAME)
    parser.add_argument("question", type=str, nargs="?")
    parser.add_argument("session_id", type=str, nargs="?")
    parser.add_argument("--show", action="store_true")
    parser.add_argument("--message")
    parser.add_argument("--model")

    namespace = parser.parse_args()

    app(namespace)


def app(namespace):
    user_id: str = "admin"
    default_session_id: str = "main_session"

    system = gpt.setup_system()
    user = system.get_user(user_id)
    session_id = namespace.session_id or default_session_id
    session = user.get_session(session_id, user.user.entity_id)
    # user.handle()


if __name__ == "__main__":
    cli()
