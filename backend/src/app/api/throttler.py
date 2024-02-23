from src.adapters.tokenbucket import TokenBucketFactory

# we probably need a throttler manager class


# TODO: make this easier to access
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

    async def validate(self, user_id: str) -> float:
        bucket = self._bucket_factory.create_bucket(
            bucket_key=user_id,
            max_tokens=self._max_tokens,
            refill_rate_s=self._refill_rate,
        )
        return await bucket.acquire(1)


def user_request_throttler(
    bucket_factory: TokenBucketFactory, max_requests: int, refill_duration_s: int
):
    """
    should we use function or class?
    function is simpler, but it does not provide good typing support
    """

    def validator(user_id: str):
        bucket = bucket_factory.create_bucket(
            bucket_key=user_id,
            max_tokens=max_requests,
            refill_rate_s=refill_duration_s,
        )
        return bucket.acquire(1)

    return validator
