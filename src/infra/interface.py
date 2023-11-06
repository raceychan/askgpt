import typing as ty

from src.domain.interface import IMessage


class Receivable(ty.Protocol):
    def receive(self, message: IMessage) -> None:
        ...
