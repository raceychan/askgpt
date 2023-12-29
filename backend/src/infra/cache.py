import abc
import datetime
import pathlib
import typing as ty
from contextlib import asynccontextmanager

from redis import asyncio as aioredis
from src.domain.base import KeySpace, freezelru

type RedisBool = ty.Literal[0, 1]


class ScriptFunc[
    KeysT: ty.Sequence[bytes | str | memoryview],
    ArgsT: ty.Iterable[str | int | float | bytes | memoryview],
    ResultT,
](ty.Protocol):
    def __call__(self, keys: KeysT, args: ArgsT) -> ty.Awaitable[ResultT]:
        ...


class Cache[TKey: ty.Hashable, TValue: ty.Any](abc.ABC):
    """
    TODO: refactor, seperate different interface from cache
    redis.Redis has all interfaces of set, list, hashmap, etc.
    but we only need some of them at a time, so we should seperate them.

    eg:
    cache.map.set
    cache.set.add
    cache.list.append

    @property
    def set(self):
        return

    """

    @abc.abstractmethod
    async def get(self, key: TKey) -> TValue | None:
        ...

    @abc.abstractmethod
    async def set(self, key: TKey, value: TValue) -> None:
        ...

    @abc.abstractmethod
    async def remove(self, key: TKey) -> None:
        ...

    @abc.abstractproperty
    def keyspace(self) -> KeySpace:
        ...


class MemoryCache[TKey: str, TVal: ty.Any](Cache[TKey, TVal]):
    def __init__(self):
        self._cache: dict[TKey, TVal] = {}

    async def get(self, key: TKey) -> TVal | None:
        return self._cache.get(key, None)

    async def set(self, key: TKey, value: TVal) -> None:
        self._cache[key] = value

    async def remove(self, key: TKey) -> None:
        self._cache.pop(key, None)

    @property
    def keyspace(self) -> KeySpace:
        return KeySpace("memory")

    @classmethod
    @freezelru
    def from_singleton(cls) -> ty.Self:
        return cls()


class RedisCache(Cache[ty.Hashable, ty.Any]):
    def __init__(self, redis: aioredis.Redis, keyspace: KeySpace):
        self._redis = redis
        self._keyspace = keyspace

    @property
    def keyspace(self) -> KeySpace:
        return self._keyspace

    @property
    def client(self):
        return self._redis

    async def get(self, key: ty.Hashable) -> ty.Any | None:
        return await self._redis.get(key)  # type: ignore

    async def set(
        self,
        key: ty.Hashable,
        value: ty.Any,
        ex: int | datetime.timedelta | None = None,
        px: int | datetime.timedelta | None = None,
        nx: bool = False,
        xx: bool = False,
        keepttl: bool = False,
        get: bool = False,
    ) -> ty.Any | None:
        return await self._redis.set(  # type: ignore
            key, value, ex=ex, px=px, nx=nx, xx=xx, keepttl=keepttl, get=get
        )

    async def remove(self, key: ty.Hashable) -> None:
        await self._redis.delete(key)  # type: ignore

    def load_script(
        self, script: str | pathlib.Path
    ) -> ScriptFunc[ty.Any, ty.Any, ty.Any]:
        if isinstance(script, pathlib.Path):
            script = script.read_text()
        return self._redis.register_script(script)

    async def sadd(self, key: ty.Hashable, *values: ty.Any) -> bool:
        res: RedisBool = await self._redis.sadd(key, *values)  # type: ignore
        return res == 1  # type: ignore

    async def sismember(self, key: ty.Hashable, member: ty.Any) -> bool:
        res: RedisBool = await self._redis.sismember(key, member)  # type: ignore
        return res == 1  # type: ignore

    async def lpop(self, key: ty.Hashable) -> ty.Any | None:
        return await self._redis.lpop(key)  # type: ignore

    async def rpush(self, key: ty.Hashable, *values: ty.Sequence[ty.Any]) -> bool:
        if not values:
            raise ValueError("values must not be empty")
        res: RedisBool = await self._redis.rpush(key, *values)  # type: ignore
        return res == 1

    @asynccontextmanager
    async def pipeline(self, transaction: bool = False):
        pipe = self._redis.pipeline(transaction=transaction)
        async with pipe:
            yield pipe

    @asynccontextmanager
    async def lifespan(self):
        try:
            yield self
        finally:
            await self._redis.aclose()

    @classmethod
    def build(
        cls,
        url: str,
        keyspace: str | KeySpace,
        decode_responses: bool = True,
        max_connections: int = 10,
    ):
        pool = aioredis.BlockingConnectionPool.from_url(  # type: ignore
            url,
            decode_responses=decode_responses,
            max_connections=max_connections,
        )
        client = aioredis.Redis.from_pool(pool)
        return cls(
            redis=client,
            keyspace=KeySpace(keyspace) if isinstance(keyspace, str) else keyspace,
        )
