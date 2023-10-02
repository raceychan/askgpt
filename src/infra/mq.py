import abc
import queue
import typing

from domain.model import Message


class Receivable(typing.Protocol):
    def receive(self, message: Message):
        ...


class MessageBroker(abc.ABC):
    @abc.abstractmethod
    def __len__(self) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def put(self, message: Message) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def get(self) -> Message:
        raise NotImplementedError

    @abc.abstractproperty
    def maxsize(self) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def register(self, subscriber: Receivable) -> None:
        raise NotImplementedError

    def broadcast(self, message: Message) -> None:
        """
        Optional method to broadcast message to all subscribers,
        only push-based MQ should implement this method
        reff:
            https://stackoverflow.com/questions/39586635/why-is-kafka-pull-based-instead-of-push-based
        """
        raise NotImplementedError


class QueueBroker(MessageBroker):
    def __init__(self, maxsize: int = 0):
        self._queue: queue.Queue[Message] = queue.Queue(maxsize)
        self._maxsize = maxsize
        self._subscribers: set[Receivable] = set()

    def __len__(self):
        return len(self._queue.queue)

    @property
    def maxsize(self):
        return self._maxsize

    @property
    def subscribes(self):
        return self._subscribers.copy()

    def put(self, message: Message) -> None:
        self._queue.put(message)

    def get(self):
        return self._queue.get()

    def broadcast(self, message: Message) -> None:
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

    def put(self, event: Message):
        self._broker.put(event)

    def get(self):
        return self._broker.get()

    @property
    def volume(self):
        return self._broker.maxsize

    def register(self, subscriber: Receivable):
        self._broker.register(subscriber)
