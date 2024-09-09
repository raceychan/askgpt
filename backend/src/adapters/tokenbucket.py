import typing as ty
from functools import cached_property

from src.adapters.cache import KeySpace, RedisBool, RedisCache, ScriptFunc

type TokenBucketScript = ScriptFunc[list[str], list[float | int], RedisBool]


class Throttler(ty.Protocol):
    async def acquire(self, cost: int = 1) -> bool:
        ...


class TokenBucket:
    "Refill tokens with refill rate evertime it gets called"

    def __init__(
        self,
        redis: RedisCache,
        bucket_script: TokenBucketScript,
        *,
        bucket_key: KeySpace,
        max_tokens: int,
        refill_rate_s: float,
    ):
        self._redis = redis
        self._bucketscript = bucket_script

        # These three are instance attributes
        self._bucket_key = bucket_key
        self._max_tokens = max_tokens
        self._refill_rate_s = refill_rate_s

    @cached_property
    def _refill_token_script(
        self,
    ) -> ScriptFunc[list[str], list[float | int], RedisBool]:
        # only refills if bucket is not full
        lua = """
        -- Refill token bucket algorithm
        -- Keys: [bucket_key]
        -- Args: [token_cost, max_tokens]

        local bucket_key = KEYS[1]
        local token_cost = tonumber(ARGV[1])
        local max_tokens = tonumber(ARGV[2])

        -- Increment the token count
        local current_tokens = tonumber(redis.call('HINCRBY', bucket_key, 'tokens', token_cost))

        -- Ensure the token count does not exceed the max limit
        if current_tokens > max_tokens then
            redis.call('HSET', bucket_key, 'tokens', max_tokens)
        end

        return true
        """
        return self._redis.load_script(lua)

    async def release(self, cost: int = 1):
        res = await self._refill_token_script(
            keys=[self._bucket_key.key], args=[cost, self._max_tokens]
        )
        return res == 1

    async def acquire(self, cost: int = 1) -> ty.Literal[0] | float:
        args = [self._max_tokens, self._refill_rate_s, cost]
        wait_time = await self._bucketscript(keys=[self._bucket_key.key], args=args)
        return wait_time

    async def reserve_token(self, token_cost: int = 1) -> None:
        raise NotImplementedError


class TokenBucketFactory:
    def __init__(
        self,
        redis: RedisCache,
        script: TokenBucketScript,
        keyspace: KeySpace | None = None,
    ):
        self.cache = redis
        self.script = script
        self.keyspace = keyspace

    def create_bucket(
        self, bucket_key: str, max_tokens: int, refill_rate_s: float
    ) -> TokenBucket:
        key_ = self.keyspace(bucket_key) if self.keyspace else KeySpace(bucket_key)
        return TokenBucket(
            self.cache,
            self.script,
            bucket_key=key_,
            max_tokens=max_tokens,
            refill_rate_s=refill_rate_s,
        )
