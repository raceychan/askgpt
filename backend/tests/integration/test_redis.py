import asyncio

import pytest

from askgpt.adapters.cache import Cache, RedisBool, RedisCache, ScriptFunc
from askgpt.adapters.tokenbucket import TokenBucket
from askgpt.domain.config import Settings
from askgpt.helpers.file import FileUtil


@pytest.fixture(scope="module")
def tokenbucket_script(redis_cache: RedisCache):
    script = FileUtil.from_cwd().find("script/tokenbucket.lua")
    return redis_cache.load_script(script)


# @pytest.fixture(scope="module")
# async def token_bucket(
#     settings: Settings,
#     cache: Cache,
#     tokenbucket_script: ScriptFunc[list[str], list[float | int], RedisBool],
# ):
#     bucket_key = settings.redis.keyspaces.APP.add_cls(TokenBucket)
#     bucket = TokenBucket(
#         cache,
#         bucket_script=tokenbucket_script,  # type: ignore
#         bucket_key=bucket_key,
#         max_tokens=2,
#         refill_rate_s=0.1,
#     )
#     yield bucket
#     await cache.remove(bucket_key.key)


# @pytest.mark.asyncio
# async def test_token_bucket_reach_limit(token_bucket: TokenBucket):
#     sem = 10
#     tasks = [asyncio.create_task(token_bucket.acquire(1)) for _ in range(sem)]
#     results = await asyncio.gather(*tasks)

#     passes = sum([res == 0 for res in results])

#     assert passes == 2 and (sem - passes) == 8
