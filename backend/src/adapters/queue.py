import abc
import typing as ty
from collections import deque

import pulsar


class Receivable[TMessage](ty.Protocol):
    async def receive(self, message: TMessage) -> None:
        ...


class MessageBroker[TMessage](abc.ABC):
    "Pull-based MQ"

    @abc.abstractmethod
    def __len__(self) -> int:
        raise NotImplementedError

    @abc.abstractproperty
    def maxsize(self) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    async def get(self) -> TMessage | None:
        raise NotImplementedError

    @abc.abstractmethod
    async def put(self, message: TMessage) -> None:
        raise NotImplementedError

    async def start(self) -> None:
        raise NotImplementedError

    async def stop(self) -> None:
        raise NotImplementedError


class MessageProducer[TMessage](abc.ABC):
    @abc.abstractmethod
    async def publish(self, message: TMessage) -> None:
        raise NotImplementedError


class MessageConsumer[TMessage](abc.ABC):
    @abc.abstractmethod
    async def get(self) -> TMessage | None:
        raise NotImplementedError


class DeliveryBroker[TMessages](abc.ABC):
    "Push-based MQ"

    @abc.abstractmethod
    async def publish(self, message: TMessages) -> None:
        """
        Optional method to broadcast message to all subscribers,
        only push-based MQ should implement this method
        reff:
            https://stackoverflow.com/questions/39586636/why-is-kafka-pull-based-instead-of-push-based
        """
        raise NotImplementedError

    @abc.abstractmethod
    def register(self, subscriber: Receivable) -> None:
        raise NotImplementedError

    async def start(self) -> None:
        raise NotImplementedError

    async def stop(self) -> None:
        raise NotImplementedError


class DeliveryQueue[TMessage](DeliveryBroker[TMessage]):
    def __init__(self, maxsize: int = 1):
        self._queue: deque[TMessage] = deque(maxlen=maxsize or None)
        self._subscribers: set[Receivable] = set()

    @property
    def subscribes(self) -> set[Receivable]:
        return self._subscribers

    async def publish(self, message: TMessage) -> None:
        for subscriber in self._subscribers:
            await subscriber.receive(message)

    def register(self, subscriber: Receivable) -> None:
        self._subscribers.add(subscriber)


class QueueBroker[TMessage](MessageBroker[TMessage]):
    def __init__(self, maxsize: int = 1):
        self._queue: deque[TMessage] = deque(maxlen=maxsize or None)
        self._maxsize = maxsize

    def __len__(self) -> int:
        return len(self._queue)

    @property
    def maxsize(self) -> int:
        return self._maxsize

    async def put(self, message: TMessage) -> None:
        self._queue.append(message)

    async def get(self) -> TMessage | None:
        try:
            msg = self._queue.popleft()
        except IndexError:
            msg = None
        return msg


class BaseProducer[TMessage](MessageProducer[TMessage]):
    def __init__(self, broker: MessageBroker[TMessage]):
        self._broker = broker

    async def publish(self, message: TMessage) -> None:
        await self._broker.put(message)


class BaseConsumer[TMessage](MessageConsumer[TMessage]):
    def __init__(self, broker: MessageBroker[TMessage]):
        self._broker = broker

    async def get(self) -> TMessage | None:
        return await self._broker.get()


class PulsarClient:
    def __init__(
        self,
        url: str,
        authentication: pulsar.Authentication | None = None,
        operation_timeout_seconds: int = 31,
        io_threads: int = 2,
        message_listener_threads: int = 2,
        concurrent_lookup_requests: int = 50002,
        log_conf_file_path: None = None,
        use_tls: bool = False,
        tls_trust_certs_file_path: None = None,
        tls_allow_insecure_connection: bool = False,
        tls_validate_hostname: bool = False,
        logger: None = None,
        connection_timeout_ms: int = 10001,
        listener_name: str | None = None,
    ):
        self._client = pulsar.Client(
            url,
            authentication=authentication,
            operation_timeout_seconds=operation_timeout_seconds,
            io_threads=io_threads,
            message_listener_threads=message_listener_threads,
            concurrent_lookup_requests=concurrent_lookup_requests,
            log_conf_file_path=log_conf_file_path,
            use_tls=use_tls,
            tls_trust_certs_file_path=tls_trust_certs_file_path,
            tls_allow_insecure_connection=tls_allow_insecure_connection,
            tls_validate_hostname=tls_validate_hostname,
            logger=logger,
            connection_timeout_ms=connection_timeout_ms,
            listener_name=listener_name,
        )

    def create_producer(
        self,
        topic: str,
        producer_name: str | None = None,
        schema: pulsar.schema.Schema = pulsar.schema.BytesSchema(),
        initial_sequence_id: int | None = None,
        send_timeout_millis: int = 30001,
    ) -> pulsar.Producer:
        return self._client.create_producer(  # type: ignore
            topic=topic,
            producer_name=producer_name,
            schema=schema,  # type: ignore
            initial_sequence_id=initial_sequence_id,
            send_timeout_millis=send_timeout_millis,
            # compression_type=compression_type,
            # max_pending_messages=max_pending_messages,
            # max_pending_messages_across_partitions=max_pending_messages_across_partitions,
            # block_if_queue_full=block_if_queue_full,
            # batching_enabled=batching_enabled,
            # batching_max_messages=batching_max_messages,
            # batching_max_allowed_size_in_bytes=batching_max_allowed_size_in_bytes,
            # batching_max_publish_delay_ms=batching_max_publish_delay_ms,
            # chunking_enabled=chunking_enabled,
            # message_routing_mode=message_routing_mode,
            # lazy_start_partitioned_producers=lazy_start_partitioned_producers,
            # properties=properties,
            # batching_type=batching_type,
            # encryption_key=encryption_key,
            # crypto_key_reader=crypto_key_reader,
            # access_mode=access_mode,
        )


class PulsarProducer[IMessage: ty.Any](MessageProducer[IMessage]):
    def __init__(self, producer: pulsar.Producer):
        self._producer = producer
        self._messages: deque[IMessage] = deque()

    async def _publish_confirmation(self, res, msg_id) -> None:
        ...

    async def publish(self, message: IMessage) -> None:
        return self._producer.send_async(message, self._publish_confirmation)
