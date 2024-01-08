import asyncio

import pytest
from src.adapters.cache import RedisBool, RedisCache, ScriptFunc
from src.adapters.tokenbucket import TokenBucket
from src.domain.config import Settings
from src.tools.fileutil import FileUtil


@pytest.fixture(scope="module")
def tokenbucket_script(redis_cache: RedisCache):
    script = FileUtil().find("script/tokenbucket.lua")
    return redis_cache.load_script(script)


@pytest.fixture(scope="module")
async def token_bucket(
    settings: Settings,
    redis_cache: RedisCache,
    tokenbucket_script: ScriptFunc[list[str], list[float | int], RedisBool],
):
    bucket_key = settings.redis.keyspaces.APP.generate_for_cls(TokenBucket)
    bucket = TokenBucket(
        redis_cache,
        bucket_script=tokenbucket_script,  # type: ignore
        bucket_key=bucket_key,
        max_tokens=2,
        refill_rate_s=0.1,
    )
    yield bucket
    await redis_cache.remove(bucket_key.key)


@pytest.mark.asyncio
async def test_token_bucket_reach_limit(token_bucket: TokenBucket):
    sem = 10
    tasks = [asyncio.create_task(token_bucket.acquire(1)) for _ in range(sem)]
    results = await asyncio.gather(*tasks)

    passes = sum([res == 0 for res in results])

    assert passes == 2 and (sem - passes) == 8
