import abc
import typing as ty

import anthropic
import httpx
import openai
from askgpt.app.gpt._errors import OpenAIRequestError
from askgpt.app.gpt.anthropic import _params as anthropic_params
from askgpt.app.gpt.openai import _params as openai_params
from askgpt.domain.types import SupportedGPTs
from askgpt.helpers._log import logger
from askgpt.helpers.functions import attribute, lru_cache
from openai._exceptions import APIStatusError
from openai.types import chat as openai_chat

MAX_RETRIES: int = 1

type ClientFactory = ty.Callable[[str], "GPTClient"]


class ClientRegistry:
    "Abstract factory of GPTClient"
    _registry: ty.ClassVar[dict[str, type["GPTClient"]]] = dict()

    def __getitem__(self, gpt_type: SupportedGPTs) -> type["GPTClient"]:
        return self._registry[gpt_type]

    @attribute
    def registry(self) -> dict[str, type["GPTClient"]]:
        return self._registry.copy()

    @classmethod
    def client_factory(cls, gpt_type: SupportedGPTs) -> type["GPTClient"]:
        try:
            client = cls._registry[gpt_type]
        except KeyError:
            raise Exception(f"Client not registered for {gpt_type}")
        return client

    @classmethod
    def register(cls, gpt_type: SupportedGPTs):
        def inner[T: type["GPTClient"]](client_cls: T) -> T:
            cls._registry[gpt_type] = client_cls
            return client_cls

        return inner


class GPTClient(ty.Protocol):
    """
    Abstract GPT client
    """

    @abc.abstractmethod
    async def complete(
        self,
        messages: list[ty.Any],
        params: dict[str, ty.Any],
    ) -> ty.AsyncGenerator[str, None]:
        yield ""
        raise NotImplementedError


class OpenAIClient(GPTClient):
    def __init__(self, client: openai.AsyncOpenAI):
        self._client = client

    @property
    def chatgpt(self):
        return self._client.chat.completions

    async def complete(
        self,
        messages: list[openai_params.CompletionMessage],
        params: openai_params.OpenAIChatMessageOptions,
    ) -> ty.AsyncGenerator[str, None]:
        s_resp: ty.AsyncIterable[openai_chat.ChatCompletionChunk]
        params["messages"] = messages
        params["stream"] = True

        try:
            s_resp = await self.chatgpt.create(**params)  # type: ignore
        except APIStatusError as e:
            raise OpenAIRequestError(e.status_code, e.message, e.body)

        if isinstance(s_resp, openai_chat.ChatCompletion):
            yield (s_resp.choices[0].message.content or "")
        else:
            s_resp = ty.cast(ty.AsyncIterable[openai_chat.ChatCompletionChunk], s_resp)
            async for chunk in s_resp:
                if not chunk.choices:
                    continue
                choice = chunk.choices[0]
                content = choice.delta.content or ""
                yield content

    @classmethod
    @lru_cache(maxsize=1000)
    def from_apikey(cls, api_key: str, timeout: float = 10.0) -> "OpenAIClient":
        return cls.build(api_key=api_key, timeout=timeout)

    @classmethod
    def build(
        cls,
        api_key: str,
        *,
        organization: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
        max_retries: int = 1,
        default_headers: ty.Mapping[str, str] | None = None,
        default_query: ty.Mapping[str, object] | None = None,
        http_client: httpx.AsyncClient | None = None,
        _strict_response_validation: bool = False,
    ) -> "OpenAIClient":
        openai_client = openai.AsyncOpenAI(
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
        return cls(openai_client)


class AnthropicClient(GPTClient):
    def __init__(self, client: anthropic.AsyncAnthropic):
        self._client = client

    async def complete(
        self,
        messages: list[anthropic_params.MessageParam],
        params: anthropic_params.AnthropicChatMessageOptions,
    ) -> ty.AsyncGenerator[str, None]:
        params["messages"] = messages
        params["stream"] = True

        resp = await self._client.messages.create(**params)
        async for chunk in resp:
            if isinstance(chunk, anthropic.types.RawContentBlockDeltaEvent):
                yield chunk.delta.text
            elif isinstance(chunk, anthropic.types.RawMessageDeltaEvent):
                if chunk.delta.stop_reason:
                    break
            else:
                yield ""
                logger.warning(f"Unknown chunk type: {type(chunk)}")

    @classmethod
    @lru_cache(maxsize=1000)
    def from_apikey(
        cls, api_key: str, timeout: float = 10.0, max_tries: int = MAX_RETRIES
    ) -> "AnthropicClient":
        return cls(
            anthropic.AsyncAnthropic(
                api_key=api_key, timeout=timeout, max_retries=max_tries
            )
        )
