import abc
import typing as ty
from collections import deque

from src.domain.model import Message


class Receivable(ty.Protocol):
    def receive(self, message: Message):
        ...


class MessageBroker(abc.ABC):
    @abc.abstractmethod
    def __len__(self) -> int:
        raise NotImplementedError

    @abc.abstractproperty
    def maxsize(self) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    async def put(self, message: Message) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def get(self) -> Message:
        raise NotImplementedError

    @abc.abstractmethod
    def register(self, subscriber: Receivable) -> None:
        raise NotImplementedError

    async def broadcast(self, message: Message) -> None:
        """
        Optional method to broadcast message to all subscribers,
        only push-based MQ should implement this method
        reff:
            https://stackoverflow.com/questions/39586635/why-is-kafka-pull-based-instead-of-push-based
        """
        raise NotImplementedError


class QueueBroker(MessageBroker):
    def __init__(self, maxsize: int = 0):
        self._queue: deque[Message] = deque(maxlen=maxsize or None)
        self._maxsize = maxsize
        self._subscribers: set[Receivable] = set()

    def __len__(self):
        return len(self._queue)

    @property
    def maxsize(self):
        return self._maxsize

    @property
    def subscribes(self):
        return self._subscribers

    async def put(self, message: Message) -> None:
        self._queue.append(message)

    async def get(self):
        return self._queue.popleft()

    async def broadcast(self, message: Message) -> None:
        for subscriber in self._subscribers:
            subscriber.receive(message)

    def register(self, subscriber: Receivable):
        self._subscribers.add(subscriber)


class MailBox:
    def __init__(self, broker: MessageBroker):
        self._broker = broker

    def __len__(self):
        return len(self._broker)

    def __bool__(self):
        return self.__len__() > 0

    async def put(self, message: Message):
        await self._broker.put(message)

    async def get(self):
        return await self._broker.get()

    async def __aiter__(self):
        yield await self.get()

    def __repr__(self):
        return f"{self.__class__.__name__}({self.size()} messages)"

    @property
    def capacity(self):
        return self._broker.maxsize

    def size(self):
        return len(self._broker)

    def register(self, subscriber: Receivable):
        self._broker.register(subscriber)

    @classmethod
    def build(cls, broker: MessageBroker | None = None, maxsize: int = 0):
        if broker is None:
            broker = QueueBroker(maxsize)
        return cls(broker)


 