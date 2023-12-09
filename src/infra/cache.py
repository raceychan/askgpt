import abc
import typing as ty
from functools import lru_cache

from redis import asyncio as aioredis


class Cache[TKey: ty.Hashable, TValue: ty.Any](abc.ABC):
    @abc.abstractmethod
    async def get(self, key: TKey) -> TValue | None:
        ...

    @abc.abstractmethod
    async def set(self, key: TKey, value: TValue) -> None:
        ...

    @abc.abstractmethod
    async def remove(self, key: TKey) -> None:
        ...


class RedisCache[TKey: str, TVal: ty.Any](Cache[TKey, TVal]):
    def __init__(self, redis: aioredis.Redis):
        self._redis = redis

    async def get(self, key: TKey) -> TVal | None:
        return await self._redis.get(key)  # type: ignore

    async def set(self, key: TKey, value: TVal) -> None:
        await self._redis.set(key, value)  # type: ignore

    async def remove(self, key: TKey) -> None:
        await self._redis.delete(key)  # type: ignore

    async def pipeline(self):
        async with self._redis.pipeline() as pipe:
            yield pipe

    @classmethod
    def from_url(cls, url: str, decode_responses: bool = True):
        client = aioredis.Redis.from_url(url, decode_responses=decode_responses)  # type: ignore
        return cls(redis=client)


class MemoryCache[TKey: str, TVal: ty.Any](Cache[TKey, TVal]):
    def __init__(self):
        self._cache: dict[TKey, TVal] = {}

    async def get(self, key: TKey) -> TVal | None:
        return self._cache.get(key, None)

    async def set(self, key: TKey, value: TVal) -> None:
        self._cache[key] = value

    async def remove(self, key: TKey) -> None:
        self._cache.pop(key, None)

    @classmethod
    @lru_cache(maxsize=1)
    def from_singleton(cls) -> ty.Self:
        return cls()
