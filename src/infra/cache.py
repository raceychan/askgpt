import abc
import typing as ty
from functools import lru_cache


class Cache[TKey, TValue](abc.ABC):
    @abc.abstractmethod
    async def get(self, key: TKey) -> TValue | None:
        ...

    @abc.abstractmethod
    async def set(self, key: TKey, value: TValue) -> None:
        ...

    @abc.abstractmethod
    async def remove(self, key: TKey) -> None:
        ...


class RemoteCache:
    ...


class LocalCache[TKey, TVal](Cache[TKey, TVal]):
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
