import asyncio

import pytest
from src.domain.config import get_setting
from src.infra.cache import RedisBool, RedisCache, ScriptFunc
from src.infra.fileutil import FileUtil
from src.infra.tokenbucket import TokenBucket


@pytest.fixture(scope="module")
async def redis_cache():
    redis = RedisCache.build(url=get_setting().redis.URL, max_connections=100)
    async with redis.lifespan() as r:
        yield r


@pytest.fixture(scope="module")
def tokenbucket_script(redis_cache: RedisCache):
    script = FileUtil().find("script/tokenbucket.lua")
    return redis_cache.load_script(script)


@pytest.fixture(scope="module")
async def token_bucket(
    redis_cache: RedisCache,
    tokenbucket_script: ScriptFunc[list[str], list[float | int], RedisBool],
):
    bucket = TokenBucket(
        redis_cache,
        tokenbucket_lua=tokenbucket_script,  # type: ignore
        bucket_key="test_bucket",
        max_tokens=2,
        refill_rate=0,
    )
    yield bucket
    await redis_cache.remove("test_bucket")


@pytest.mark.asyncio
async def test_token_bucket_reach_limit(token_bucket: TokenBucket):
    sem = 10
    tasks = [asyncio.create_task(token_bucket.acquire(1)) for _ in range(sem)]
    results = await asyncio.gather(*tasks)

    trues = sum(results)
    assert trues == 2 and (sem - trues) == 8
