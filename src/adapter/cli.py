from argparse import ArgumentParser

from src.app.service import event_listener, gpt
from src.domain.config import Settings

system = gpt.setup_system()


def cli():
    parser = ArgumentParser(description="gpt client in zen mode")
    parser.add_argument("question", type=str, nargs="?")
    parser.add_argument("session_id", type=str, nargs="?")
    parser.add_argument("--model")
    namespace = parser.parse_args()

    app(namespace)


def app(namespace):
    user_id: str = "admin"
    default_session_id: str = "main_session"

    user = system.get_user(user_id)

    # answer = user.ask_question(namespace.question, default_session_id)
    answer = user.ask_question(namespace.question, default_session_id)
    # session_id = namespace.session_id or default_session_id
    # session = user.get_session(session_id, user.user.entity_id)
    # user.handle()


def user_send_question():
    ...


if __name__ == "__main__":
    cli()
