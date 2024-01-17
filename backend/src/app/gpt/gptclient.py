import abc
import typing as ty
from collections import deque
from contextlib import asynccontextmanager

import httpx
import openai
from openai.types import beta as openai_beta
from openai.types import chat as openai_chat

from src.adapters import cache
from src.app.gpt import model, params
from src.domain.base import SupportedGPTs
from src.toolkit.funcutils import attribute, lru_cache

MAX_RETRIES: int = 3


class GPTClient(abc.ABC):
    async def complete(
        self,
        messages: list[model.ChatMessage],
        model: model.CompletionModels,
        user: str,
        stream: bool,
        options: params.CompletionOptions,  # type: ignore
    ) -> ty.AsyncIterable[openai_chat.ChatCompletionChunk]:
        ...

    @classmethod
    @lru_cache(maxsize=1000)
    @abc.abstractmethod
    def from_apikey(cls, api_key: str) -> ty.Self:
        ...


class ClientRegistry:
    "Abstract factory of GPTClient"
    _registry: ty.ClassVar[dict[str, type[GPTClient]]] = dict()

    def __getitem__(self, gpt_type: SupportedGPTs) -> type["GPTClient"]:
        return self._registry[gpt_type]

    @attribute
    def registry(self) -> dict[str, type[GPTClient]]:
        return self._registry.copy()

    @classmethod
    def client_factory(cls, gpt_type: SupportedGPTs) -> type[GPTClient]:
        try:
            client = cls._registry[gpt_type]
        except KeyError:
            raise Exception(f"Client not registered for {gpt_type}")
        return client

    @classmethod
    def register(cls, gpt_type: SupportedGPTs):
        def inner[T: type[GPTClient]](client_cls: T) -> T:
            cls._registry[gpt_type] = client_cls
            return client_cls

        return inner


@ClientRegistry.register("openai")
class OpenAIClient(GPTClient):
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

    async def complete(
        self,
        messages: list[model.ChatMessage],
        model: model.CompletionModels,
        user: str,
        stream: bool,
        options: params.CompletionOptions,  # type: ignore
    ) -> ty.AsyncIterable[openai_chat.ChatCompletionChunk]:
        msgs = self.message_adapter(messages)
        resp: ty.AsyncIterable[
            openai_chat.ChatCompletionChunk
        ] = await self._client.chat.completions.create(
            messages=msgs,  # type: ignore
            model=model,
            stream=stream,
            user=user,
            **options,
        )
        assert isinstance(resp, ty.AsyncIterable)
        return resp

    def message_adapter(
        self, messages: list[model.ChatMessage]
    ) -> list[dict[str, ty.Any]]:
        return [message.asdict(exclude={"user_id"}) for message in messages]

    @classmethod
    @lru_cache(maxsize=1000)
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
