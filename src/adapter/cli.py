import typing as ty
from argparse import ArgumentParser

from src.app.service import gpt
from src.domain.config import Settings


def app(namespace):
    ...


def cli():
    settings = Settings.from_file()

    parser = ArgumentParser(prog=settings.PROJECT_NAME)
    parser.add_argument("--show", action="store_true")
    parser.add_argument("--message")
    parser.add_argument("--model")

    namespace = parser.parse_args()

    app(namespace)
