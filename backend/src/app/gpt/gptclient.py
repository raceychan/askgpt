import abc
import typing as ty
from collections import deque
from contextlib import asynccontextmanager
from functools import cache, cached_property

import httpx
import openai
from openai.types import beta as openai_beta
from openai.types import chat as openai_chat
from src.app.gpt import model, params
from src.infra.cache import RedisBool, RedisCache, ScriptFunc

MAX_RETRIES: int = 3


class AIClient(abc.ABC):
    ...


class OpenAIClient(AIClient):
    def __init__(self, client: openai.AsyncOpenAI):
        self._client = client

    async def assistant(
        self,
        model: str,
        name: str,
        instructions: str,
        tools: list[openai_beta.assistant_create_params.Tool],
    ) -> openai_beta.Assistant:
        return await self._client.beta.assistants.create(
            model=model, name=name, instructions=instructions, tools=tools
        )

    async def create_thread(self) -> openai_beta.Thread:
        """
        https://platform.openai.com/docs/assistants/overview
        """
        return await self._client.beta.threads.create()

    async def send_chat(
        self,
        messages: list[model.ChatMessage],
        model: model.CompletionModels,
        user: str,
        stream: bool = True,
        **options: ty.Unpack[params.CompletionOptions],  # type: ignore
    ) -> ty.AsyncGenerator[openai_chat.ChatCompletionChunk, None]:
        msgs = self.message_adapter(messages)
        resp = await self._client.chat.completions.create(  # type: ignore
            messages=msgs,  # type: ignore
            model=model,
            stream=stream,
            user=user,
            **options,
        )

        return resp  # type: ignore

    def message_adapter(
        self, messages: list[model.ChatMessage]
    ) -> list[dict[str, ty.Any]]:
        return [message.asdict(exclude={"user_id"}) for message in messages]

    @classmethod
    @cache
    def from_apikey(cls, api_key: str) -> ty.Self:
        client = openai.AsyncOpenAI(api_key=api_key)
        return cls(client=client)

    @classmethod
    def build(
        cls,
        api_key: str,
        *,
        organization: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
        max_retries: int = MAX_RETRIES,
        default_headers: ty.Mapping[str, str] | None = None,
        default_query: ty.Mapping[str, object] | None = None,
        http_client: httpx.AsyncClient | None = None,
        _strict_response_validation: bool = False,
    ) -> openai.AsyncOpenAI:
        return openai.AsyncOpenAI(
            api_key=api_key,
            organization=organization,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
            default_query=default_query,
            http_client=http_client,
            _strict_response_validation=_strict_response_validation,
        )


# https://medium.com/@colemanhindes/unofficial-gpt-3-developer-faq-fcb770710f42
# Only 2 concurrent requests can be made per API key at a time.
class APIPool:
    def __init__(self, pool_key: str, api_keys: ty.Sequence[str], redis: RedisCache):
        self.pool_key = pool_key
        self.api_keys = deque(api_keys)
        self._redis = redis
        self._client_cache: dict[str, OpenAIClient] = {}
        self.__started: bool = False

    @property
    def is_started(self) -> bool:
        return self.__started

    async def acquire(self):
        # Pop an API key from the front of the deque
        if not self.__started:
            raise Exception("APIPool not started")
        api_key = await self._redis.lpop(self.pool_key)
        if not api_key:
            raise Exception("No API keys available")
        return api_key

    async def release(self, api_key: str):
        # Push the API key back to the end of the deque
        await self._redis.rpush(self.pool_key, api_key)

    @asynccontextmanager
    async def reserve_client(self):
        # TODO: create corresponding ai client from api keytype
        api_key = await self.acquire()

        try:
            if client := self._client_cache.get(api_key):
                yield client
            else:
                client = OpenAIClient.from_apikey(api_key)
                self._client_cache[api_key] = client
            yield client
        finally:
            await self.release(api_key)

    @asynccontextmanager
    async def lifespan(self):
        try:
            await self.start()
            yield self
        finally:
            await self.close()

    async def start(self):
        if not self.api_keys:
            raise Exception("No API keys in the pool")
        await self._redis.rpush(self.pool_key, *self.api_keys)
        self.__started = True

    async def close(self):
        # remove api keys from redis, clear client cache
        await self._redis.remove(self.pool_key)
        self.__started = False


class TokenBucket:
    def __init__(
        self,
        redis: RedisCache,
        tokenbucket_lua: ScriptFunc[list[str], list[float | int], RedisBool],
        *,
        bucket_key: str,  # based on user_id
        max_tokens: int,
        refill_rate: float,
    ):
        self.redis = redis
        self.bucket_key = bucket_key
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate
        self.tokenbucket = tokenbucket_lua

    @cached_property
    def _refill_token_script(
        self,
    ) -> ScriptFunc[list[str], list[float | int], RedisBool]:
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
        return self.redis.load_script(lua)

    async def release(self, token_cost: int = 1):
        res = await self._refill_token_script(
            keys=[self.bucket_key], args=[token_cost, self.max_tokens]
        )
        return res == 1

    async def acquire(self, token_cost: int = 1) -> bool:
        args = [self.max_tokens, self.refill_rate, token_cost]
        res = await self.tokenbucket(keys=[self.bucket_key], args=args)
        return res == 1

    async def reserve_token(self, token_cost: int = 1) -> None:
        raise NotImplementedError
