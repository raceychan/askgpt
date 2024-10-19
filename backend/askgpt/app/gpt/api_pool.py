import typing as ty
from contextlib import asynccontextmanager

from askgpt.adapters import cache
from askgpt.app.gpt.errors import APIKeyNotAvailableError
from askgpt.domain.types import SupportedGPTs


class PoolFacotry:
    pool_keyspace: cache.KeySpace
    api_type: SupportedGPTs
    cache: cache.Cache[str, str]


# https://medium.com/@colemanhindes/unofficial-gpt-3-developer-faq-fcb770710f42
# Only 2 concurrent requests can be made per API key at a time.
class APIPool:
    # TODO: refactor this to be an infra component used by gpt service
    def __init__(
        self,
        *,
        pool_keyspace: cache.KeySpace,
        api_type: str,
        api_keys: ty.Sequence[str],
        cache: cache.Cache[str, str],
    ):
        self._pool_key = pool_keyspace
        self._api_type = api_type
        self._api_keys = api_keys
        self._cache = cache

    async def acquire(self):
        # Pop an API key from the front of the deque
        api_key = await self._cache.lpop(self._pool_key.key)
        if not api_key:
            raise APIKeyNotAvailableError(self._api_type)
        return api_key

    async def release(self, api_key: str):
        # Push the API key back to the end of the deque
        await self._cache.rpush(self._pool_key.key, api_key)

    async def load_keys(self, keys: ty.Sequence[str]):
        # BUG: should check length of api_pool before pushing
        # else:
        await self._cache.rpush(self._pool_key.key, *keys)

    @asynccontextmanager
    async def reserve_api_key(self):
        # TODO: use redis transaction/lock
        await self.load_keys(self._api_keys)
        api_key = await self.acquire()
        try:
            yield api_key
        finally:
            await self.release(api_key)
