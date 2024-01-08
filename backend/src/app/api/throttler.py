from src.adapters.tokenbucket import TokenBucketFactory


# TODO: make this an application level dependency
class UserRequestThrottler:
    def __init__(
        self,
        bucket_factory: TokenBucketFactory,
        max_requests: int,
        refill_duration_s: int,
    ):
        self._bucket_factory = bucket_factory
        self._max_tokens = max_requests
        self._refill_rate = max_requests / refill_duration_s

    @property
    def max_tokens(self):
        return self._max_tokens

    async def validate_request(self, user_id: str):
        bucket = self._bucket_factory.create_bucket(
            bucket_key=user_id,
            max_tokens=self._max_tokens,
            refill_rate_s=self._refill_rate,
        )
        return await bucket.acquire(1)
