from functools import cached_property

from src.infra.cache import RedisBool, RedisCache, ScriptFunc

type TokenBucketScript = ScriptFunc[list[str], list[float | int], RedisBool]


class TokenBucket:
    "Refill tokens with refill rate evertime it gets called"

    def __init__(
        self,
        redis: RedisCache,
        tokenbucket_lua: TokenBucketScript,
        *,
        bucket_key: str,
        max_tokens: int,
        refill_rate: float,
    ):
        self._redis = redis
        self._tokenbucket = tokenbucket_lua

        # These three are instance attributes
        self._bucket_key = bucket_key
        self._max_tokens = max_tokens
        self._refill_rate = refill_rate

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

    async def release(self, token_cost: int = 1):
        res = await self._refill_token_script(
            keys=[self._bucket_key], args=[token_cost, self._max_tokens]
        )
        return res == 1

    async def acquire(self, token_cost: int = 1) -> bool:
        args = [self._max_tokens, self._refill_rate, token_cost]
        res = await self._tokenbucket(keys=[self._bucket_key], args=args)
        return res == 1

    async def reserve_token(self, token_cost: int = 1) -> None:
        raise NotImplementedError


#


class BucketFactory:
    def __init__(self, redis: RedisCache, script: TokenBucketScript, namespace: str):
        self.redis = redis
        self.script = script
        self.namespace = namespace

    def create_bucket(
        self, bucket_key: str, max_tokens: int, refill_rate: float
    ) -> TokenBucket:
        return TokenBucket(
            self.redis,
            self.script,
            bucket_key=bucket_key,
            max_tokens=max_tokens,
            refill_rate=refill_rate,
        )
