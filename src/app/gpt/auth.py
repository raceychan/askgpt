import typing as ty

from src.app.actor import System
from src.app.gpt.model import User, UserCreated


class UserSystem(System[ty.Any]):
    def create_user(self, command: UserCreated) -> User:
        ...
