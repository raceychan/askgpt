import typing as ty
from collections import deque
from contextlib import asynccontextmanager

from askgpt.adapters import cache
from askgpt.domain.base import SupportedGPTs


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
        self.pool_key = pool_keyspace
        self.api_type = api_type
        self.api_keys = deque(api_keys)
        self._cache = cache
        self._keys_loaded: bool = False

    async def acquire(self):
        # Pop an API key from the front of the deque
        if not self._keys_loaded:
            raise Exception("APIPool not started")
        api_key = await self._cache.lpop(self.pool_key.key)
        if not api_key:
            raise Exception("No API keys available")
        return api_key

    async def release(self, api_key: str):
        # Push the API key back to the end of the deque
        await self._cache.rpush(self.pool_key.key, api_key)

    async def load_keys(self, keys: ty.Sequence[str]):
        await self._cache.rpush(self.pool_key.key, *keys)
        self._keys_loaded = True

    @asynccontextmanager
    async def reserve_api_key(self):
        if not self._keys_loaded:
            await self.load_keys(self.api_keys)
        api_key = await self.acquire()
        try:
            yield api_key
        finally:
            await self.release(api_key)
