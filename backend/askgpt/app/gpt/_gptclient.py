import abc

# import asyncio
import typing as ty

import httpx
import openai
from openai._exceptions import APIStatusError
from openai.types import beta as openai_beta
from openai.types import chat as openai_chat

from askgpt.app.gpt._errors import OpenAIRequestError
from askgpt.app.gpt._params import ChatCompletionMessageParam, CompletionOptions
from askgpt.domain.types import SupportedGPTs
from askgpt.helpers._log import logger
from askgpt.helpers.functions import attribute, lru_cache

MAX_RETRIES: int = 3

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

    @classmethod
    @abc.abstractmethod
    def from_apikey(cls, api_key: str) -> ty.Self: ...


class OpenAIClient:
    def __init__(self, client: openai.AsyncOpenAI):
        self._client = client

    async def assistant(
        self,
        model: str,
        name: str,
        instructions: str,
        tools: list[openai_beta.assistant_tool_param.AssistantToolParam],
    ) -> openai_beta.Assistant:
        return await self._client.beta.assistants.create(
            model=model, name=name, instructions=instructions, tools=tools
        )

    async def create_thread(self) -> openai_beta.Thread:
        """
        https://platform.openai.com/docs/assistants/overview
        """
        return await self._client.beta.threads.create()

    @property
    def chatgpt(self):
        return self._client.chat.completions

    async def complete(
        self,
        messages: list[ChatCompletionMessageParam],
        params: CompletionOptions,
    ) -> ty.AsyncGenerator[str, None]:
        # ty.AsyncIterable[openai_chat.ChatCompletionChunk] | openai_chat.ChatCompletion:
        params["max_tokens"] = 10
        s_resp: ty.AsyncIterable[openai_chat.ChatCompletionChunk]
        try:
            s_resp = await self.chatgpt.create(stream=False, messages=messages, **params)  # type: ignore
        except APIStatusError as e:
            raise OpenAIRequestError(e.status_code, e.message)

        if isinstance(s_resp, openai_chat.ChatCompletion):
            yield (s_resp.choices[0].message.content or "")
        else:
            s_resp = ty.cast(ty.AsyncIterable[openai_chat.ChatCompletionChunk], s_resp)
            async for chunk in s_resp:
                logger.success(f"chunk: {chunk}")
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
        max_retries: int = MAX_RETRIES,
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
