import abc
import datetime
import functools
import pathlib
import typing as ty
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Any

from redis import asyncio as aioredis

from askgpt.helpers.string import KeySpace

type RedisBool = ty.Literal[0, 1]


class ScriptFunc[
    KeysT: ty.Sequence[bytes | str | memoryview],
    ArgsT: ty.Iterable[str | int | float | bytes | memoryview],
    ResultT,
](ty.Protocol):
    def __call__(self, keys: KeysT, args: ArgsT) -> ty.Awaitable[ResultT]: ...


class CacheList[TKey, TValue]:
    def __init__(self, base: "Cache[TKey, TValue]"):
        self._base = base
        self._cache_lists: dict[TKey, list[TValue]] = defaultdict(list)

    async def lpop(self, key: TKey) -> TValue | None:
        try:
            return self._cache_lists[key].pop(0)
        except IndexError:
            return None

    async def rpop(self, key: TKey) -> TValue | None:
        try:
            return self._cache_lists[key].pop(-1)
        except IndexError:
            return None

    async def lpush(self, key: TKey, *values: TValue) -> bool:
        self._cache_lists[key].insert(0, *values)
        return True

    async def rpush(self, key: TKey, *values: TValue) -> bool:
        self._cache_lists[key].extend(values)
        return True


class Cache[TKey: ty.Hashable, TValue: ty.Any](abc.ABC):
    @abc.abstractmethod
    async def get(self, key: TKey) -> TValue | None: ...

    @abc.abstractmethod
    async def set(self, key: TKey, value: TValue) -> None: ...

    @abc.abstractmethod
    async def remove(self, key: TKey) -> None: ...

    @abc.abstractmethod
    async def rpush(self, key: TKey, *values: TValue) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    async def rpop(self, key: TKey) -> TValue | None:
        raise NotImplementedError

    @abc.abstractmethod
    async def lpop(self, key: TKey) -> TValue | None:
        raise NotImplementedError

    @abc.abstractmethod
    async def close(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def sismember(self, key: TKey, member: ty.Any) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    async def sadd(self, key: TKey, *values: ty.Any) -> bool:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def keyspace(self) -> KeySpace: ...

    def load_script(self, script: str | pathlib.Path) -> ScriptFunc: ...
class MemoryCache[TKey: str, TVal: ty.Any](Cache[TKey, TVal]):
    def __init__(self):
        self._cache: dict[TKey, TVal] = {}
        self._set: set[TVal] = set()

    @functools.cached_property
    def list(self) -> CacheList[TKey, TVal]:
        return CacheList(self)

    @property
    def keyspace(self) -> KeySpace:
        return KeySpace("memory")

    async def get(self, key: TKey) -> TVal | None:
        return self._cache.get(key, None)

    async def set(self, key: TKey, value: TVal) -> None:
        self._cache[key] = value

    async def remove(self, key: TKey) -> None:
        self._cache.pop(key, None)

    async def rpush(self, key: TKey, *values: TVal) -> bool:
        await self.list.rpush(key, *values)
        return True

    async def rpop(self, key: TKey) -> TVal | None:
        return await self.list.rpop(key)

    async def lpop(self, key: TKey) -> TVal | None:
        return await self.list.lpop(key)

    async def sismember(self, key: TKey, member: Any) -> bool:
        return member in self._set

    async def sadd(self, key: TKey, *values: Any) -> bool:
        self._set.add(*values)
        return True

    async def close(self):
        self._cache.clear()

    @classmethod
    @functools.lru_cache(maxsize=1)
    def from_singleton(cls) -> ty.Self:
        return cls()


class RedisCache[TKey: str | memoryview | bytes](Cache[TKey, ty.Any]):
    def __init__(self, redis: aioredis.Redis, keyspace: KeySpace):
        self._redis = redis
        self._keyspace = keyspace

    @property
    def keyspace(self) -> KeySpace:
        return self._keyspace

    @property
    def client(self):
        return self._redis

    async def get(self, key: TKey) -> ty.Any | None:
        return await self._redis.get(key)  # type: ignore

    async def set(
        self,
        key: TKey,
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

    async def remove(self, key: TKey) -> None:
        await self._redis.delete(key)  # type: ignore

    def load_script(
        self, script: str | pathlib.Path
    ) -> ScriptFunc[ty.Any, ty.Any, ty.Any]:
        if isinstance(script, pathlib.Path):
            script = script.read_text()

        return self._redis.register_script(script)

    async def sadd(self, key: TKey, *values: ty.Any) -> bool:
        res: RedisBool = await self._redis.sadd(key, *values)  # type: ignore
        return res == 1  # type: ignore

    async def sismember(self, key: TKey, member: ty.Any) -> bool:
        res: RedisBool = await self._redis.sismember(key, member)  # type: ignore
        return res == 1  # type: ignore

    async def lpop(self, key: TKey) -> ty.Any | None:
        return await self._redis.lpop(key)  # type: ignore

    async def rpop(self, key: TKey) -> ty.Any | None:
        return await self._redis.rpop(key)  # type: ignore

    async def rpush(self, key: TKey, *values: ty.Sequence[ty.Any]) -> bool:
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
        await self._redis.ping()  # type: ignore
        try:
            yield self
        finally:
            await self.close()

    async def close(self):
        await self._redis.aclose(close_connection_pool=True)

    @classmethod
    def build(
        cls,
        url: str,
        keyspace: str | KeySpace,
        decode_responses: bool,
        max_connections: int,
        socket_timeout: int,
        socket_connect_timeout: int,
    ):
        pool = aioredis.BlockingConnectionPool.from_url(  # type: ignore
            url,
            decode_responses=decode_responses,
            max_connections=max_connections,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
        )
        client = aioredis.Redis.from_pool(pool)
        return cls(
            redis=client,
            keyspace=KeySpace(keyspace) if isinstance(keyspace, str) else keyspace,
        )
