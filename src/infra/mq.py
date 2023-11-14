import abc
import typing as ty
from collections import deque

from src.domain.interface import IMessage
from src.infra.interface import Receivable


class MessageBroker[TMessages: IMessage](abc.ABC):
    @abc.abstractmethod
    def __len__(self) -> int:
        raise NotImplementedError

    @abc.abstractproperty
    def maxsize(self) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    async def put(self, message: TMessages) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def get(self) -> TMessages:
        raise NotImplementedError

    @abc.abstractmethod
    def register(self, subscriber: Receivable) -> None:
        raise NotImplementedError

    async def broadcast(self, message: TMessages) -> None:
        """
        Optional method to broadcast message to all subscribers,
        only push-based MQ should implement this method
        reff:
            https://stackoverflow.com/questions/39586635/why-is-kafka-pull-based-instead-of-push-based
        """
        raise NotImplementedError


class QueueBroker(MessageBroker[IMessage]):
    def __init__(self, maxsize: int = 0):
        self._queue: deque[IMessage] = deque(maxlen=maxsize or None)
        self._maxsize = maxsize
        self._subscribers: set[Receivable] = set()

    def __len__(self) -> int:
        return len(self._queue)

    @property
    def maxsize(self) -> int:
        return self._maxsize

    @property
    def subscribes(self) -> set[Receivable]:
        return self._subscribers

    async def put(self, message: IMessage) -> None:
        self._queue.append(message)

    async def get(self) -> IMessage:
        return self._queue.popleft()

    async def broadcast(self, message: IMessage) -> None:
        for subscriber in self._subscribers:
            subscriber.receive(message)

    def register(self, subscriber: Receivable) -> None:
        self._subscribers.add(subscriber)


class MailBox:
    def __init__(self, broker: MessageBroker[IMessage]):
        self._broker = broker

    def __len__(self) -> int:
        return len(self._broker)

    def __bool__(self) -> bool:
        return self.__len__() > 0

    async def put(self, message: IMessage) -> None:
        await self._broker.put(message)

    async def get(self) -> IMessage:
        return await self._broker.get()

    async def __aiter__(self) -> ty.AsyncGenerator[IMessage, ty.Any]:
        yield await self.get()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.size()} messages)"

    @property
    def capacity(self) -> int:
        return self._broker.maxsize

    def size(self) -> int:
        return len(self._broker)

    def register(self, subscriber: Receivable) -> None:
        self._broker.register(subscriber)

    @classmethod
    def build(
        cls, broker: MessageBroker[IMessage] | None = None, maxsize: int = 0
    ) -> ty.Self:
        if broker is None:
            broker = QueueBroker(maxsize)
        return cls(broker)
