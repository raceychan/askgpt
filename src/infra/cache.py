import abc
import datetime
import pathlib
import typing as ty
from contextlib import asynccontextmanager
from functools import lru_cache

from redis import asyncio as aioredis

type KeyBuilder = ty.Callable[[str, str, str], str]
type RedisBool = ty.Literal[0, 1]


def keybuilder(projectname: str, module: str, key: str) -> str:
    return f"{projectname}:{module}:{key}"


class ScriptFunc[
    KeysT: ty.Sequence[bytes | str | memoryview],
    ArgsT: ty.Iterable[str | int | float | bytes | memoryview],
    ResultT,
](ty.Protocol):
    def __call__(self, keys: KeysT, args: ArgsT) -> ty.Awaitable[ResultT]:
        ...


class Cache[TKey: ty.Hashable, TValue: ty.Any](abc.ABC):
    """
    TODO: refactor

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


class RedisCache[TKey: str, TVal: ty.Any](Cache[TKey, TVal]):
    def __init__(self, redis: aioredis.Redis):
        self._redis = redis

    @property
    def client(self):
        return self._redis

    async def get(self, key: TKey) -> TVal | None:
        return await self._redis.get(key)  # type: ignore

    async def set(
        self,
        key: TKey,
        value: TVal,
        ex: int | datetime.timedelta | None = None,
        px: int | datetime.timedelta | None = None,
        nx: bool = False,
        xx: bool = False,
        keepttl: bool = False,
        get: bool = False,
    ) -> TVal | None:
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

    async def sadd(self, key: TKey, *values: TVal) -> bool:
        res: RedisBool = await self._redis.sadd(key, *values)  # type: ignore
        return res == 1  # type: ignore

    async def sismember(self, key: TKey, member: TVal) -> bool:
        res: RedisBool = await self._redis.sismember(key, member)  # type: ignore
        return res == 1  # type: ignore

    async def lpop(self, key: TKey) -> list[TVal] | None:
        return await self._redis.lpop(key)  # type: ignore

    async def rpush(self, key: TKey, *values: TVal) -> bool:
        res = await self._redis.rpush(key, *values)  # type: ignore
        return res == 1  # type: ignore

    # async def hmget(self, key: TKey, *fields: str) -> list[TVal | None]:
    #     return await self._redis.hmget(key, *fields)  # type: ignore

    # async def hmset(self, key: TKey, mapping: dict[str, ty.Any]) -> None:
    #     await self._redis.hmset(key, mapping)  # type: ignore

    # async def hget(self, key: TKey, field: str) -> TVal | None:
    #     return await self._redis.hget(key, field)  # type: ignore

    # async def hincrby(self, key: TKey, field: str, amount: int) -> bool:
    #     res: IntBool = await self._redis.hincrby(key, field, amount)  # type: ignore
    #     return res == 1

    # async def decrby(self, key: TKey, amount: int = 1) -> bool:
    #     res: IntBool = await self._redis.decrby(key, amount)  # type: ignore
    #     return res == 1  # type: ignore

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
    def build(cls, url: str, decode_responses: bool = True, max_connections: int = 10):
        pool = aioredis.BlockingConnectionPool.from_url(  # type: ignore
            url,
            decode_responses=decode_responses,
            max_connections=max_connections,
        )
        client = aioredis.Redis.from_pool(pool)
        return cls(redis=client)
