import typing as ty

from src.domain.interface import IMessage


class Receivable(ty.Protocol):
    async def receive(self, message: IMessage) -> None:
        ...
