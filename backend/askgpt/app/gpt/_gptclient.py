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
        if messages:
            params["messages"] = messages
        if not params.get("stream"):
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
        if messages:
            params["messages"] = messages
        if not params.get("stream"):
            params["stream"] = True

        resp = await self._client.messages.create(**params)

        async for chunk in resp:
            try:
                yield self.content_switch(chunk)
            except Exception:
                breakpoint()

    def content_switch(self, chunk: anthropic.types.RawMessageStreamEvent) -> str:
        if isinstance(chunk, anthropic.types.RawMessageStartEvent):
            return chunk.message.content[0].text
        elif isinstance(chunk, anthropic.types.RawMessageDeltaEvent):
            return ""
        elif isinstance(chunk, anthropic.types.RawMessageStopEvent):
            return ""
        elif isinstance(chunk, anthropic.types.RawContentBlockStartEvent):
            return chunk.content_block.text
        elif isinstance(chunk, anthropic.types.RawContentBlockDeltaEvent):
            return chunk.delta.text
        elif isinstance(chunk, anthropic.types.RawContentBlockStopEvent):
            return ""
        else:
            raise ValueError(f"Unknown chunk type: {type(chunk)}")

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


"""
2024-10-21 04:22:15 | INFO     | askgpt.app.gpt._gptclient:complete:158 | {'delta': TextDelta(text='I', type='text_delta'), 
'index': 0, 'type': 'content_block_delta'} | request_id=10cec96f-60a8-4373-a7ed-3bc0ed1a9b99
2024-10-21 04:22:15 | INFO     | askgpt.app.gpt._gptclient:complete:158 | {'delta': TextDelta(text=' apolog', 
type='text_delta'), 'index': 0, 'type': 'content_block_delta'} | request_id=10cec96f-60a8-4373-a7ed-3bc0ed1a9b99
2024-10-21 04:22:15 | INFO     | askgpt.app.gpt._gptclient:complete:158 | {'delta': TextDelta(text='ize, but "', 
type='text_delta'), 'index': 0, 'type': 'content_block_delta'} | request_id=10cec96f-60a8-4373-a7ed-3bc0ed1a9b99
2024-10-21 04:22:15 | INFO     | askgpt.app.gpt._gptclient:complete:158 | {'delta': TextDelta(text='sdf" doesn', 
type='text_delta'), 'index': 0, 'type': 'content_block_delta'} | request_id=10cec96f-60a8-4373-a7ed-3bc0ed1a9b99
2024-10-21 04:22:15 | INFO     | askgpt.app.gpt._gptclient:complete:158 | {'delta': TextDelta(text="'t have", 
type='text_delta'), 'index': 0, 'type': 'content_block_delta'} | request_id=10cec96f-60a8-4373-a7ed-3bc0ed1a9b99
2024-10-21 04:22:15 | INFO     | askgpt.app.gpt._gptclient:complete:158 | {'delta': TextDelta(text=' any specific', 
type='text_delta'), 'index': 0, 'type': 'content_block_delta'} | request_id=10cec96f-60a8-4373-a7ed-3bc0ed1a9b99
2024-10-21 04:22:15 | INFO     | askgpt.app.gpt._gptclient:complete:158 | {'delta': TextDelta(text=' meaning or', 
type='text_delta'), 'index': 0, 'type': 'content_block_delta'} | request_id=10cec96f-60a8-4373-a7ed-3bc0ed1a9b99
2024-10-21 04:22:15 | INFO     | askgpt.app.gpt._gptclient:complete:158 | {'delta': TextDelta(text=' context', 
type='text_delta'), 'index': 0, 'type': 'content_block_delta'} | request_id=10cec96f-60a8-4373-a7ed-3bc0ed1a9b99
2024-10-21 04:22:15 | INFO     | askgpt.app.gpt._gptclient:complete:158 | {'delta': TextDelta(text='.', type='text_delta'), 
'index': 0, 'type': 'content_block_delta'} | request_id=10cec96f-60a8-4373-a7ed-3bc0ed1a9b99
2024-10-21 04:22:15 | INFO     | askgpt.app.gpt._gptclient:complete:158 | {'delta': TextDelta(text=' It', 
type='text_delta'), 'index': 0, 'type': 'content_block_delta'} | request_id=10cec96f-60a8-4373-a7ed-3bc0ed1a9b99
2024-10-21 04:22:15 | INFO     | askgpt.app.gpt._gptclient:complete:158 | {'delta': TextDelta(text=' appears', 
type='text_delta'), 'index': 0, 'type': 'content_block_delta'} | request_id=10cec96f-60a8-4373-a7ed-3bc0ed1a9b99
2024-10-21 04:22:15 | INFO     | askgpt.app.gpt._gptclient:complete:158 | {'delta': TextDelta(text=' to be a', 
type='text_delta'), 'index': 0, 'type': 'content_block_delta'} | request_id=10cec96f-60a8-4373-a7ed-3bc0ed1a9b99
2024-10-21 04:22:16 | INFO     | askgpt.app.gpt._gptclient:complete:158 | {'delta': TextDelta(text=' random combination', 
type='text_delta'), 'index': 0, 'type': 'content_block_delta'} | request_id=10cec96f-60a8-4373-a7ed-3bc0ed1a9b99
2024-10-21 04:22:16 | INFO     | askgpt.app.gpt._gptclient:complete:158 | {'delta': TextDelta(text=' of letters.', 
type='text_delta'), 'index': 0, 'type': 'content_block_delta'} | request_id=10cec96f-60a8-4373-a7ed-3bc0ed1a9b99
2024-10-21 04:22:16 | INFO     | askgpt.app.gpt._gptclient:complete:158 | {'delta': TextDelta(text=' If', 
type='text_delta'), 'index': 0, 'type': 'content_block_delta'} | request_id=10cec96f-60a8-4373-a7ed-3bc0ed1a9b99
2024-10-21 04:22:16 | INFO     | askgpt.app.gpt._gptclient:complete:158 | {'delta': TextDelta(text=' you have', 
type='text_delta'), 'index': 0, 'type': 'content_block_delta'} | request_id=10cec96f-60a8-4373-a7ed-3bc0ed1a9b99
2024-10-21 04:22:16 | INFO     | askgpt.app.gpt._gptclient:complete:158 | {'delta': TextDelta(text=' a question', 
type='text_delta'), 'index': 0, 'type': 'content_block_delta'} | request_id=10cec96f-60a8-4373-a7ed-3bc0ed1a9b99
2024-10-21 04:22:16 | INFO     | askgpt.app.gpt._gptclient:complete:158 | {'delta': TextDelta(text=' or need assistance', 
type='text_delta'), 'index': 0, 'type': 'content_block_delta'} | request_id=10cec96f-60a8-4373-a7ed-3bc0ed1a9b99
2024-10-21 04:22:16 | INFO     | askgpt.app.gpt._gptclient:complete:158 | {'delta': TextDelta(text=' with something, 
please', type='text_delta'), 'index': 0, 'type': 'content_block_delta'} | request_id=10cec96f-60a8-4373-a7ed-3bc0ed1a9b99
2024-10-21 04:22:16 | INFO     | askgpt.app.gpt._gptclient:complete:158 | {'delta': TextDelta(text=' provide more 
information', type='text_delta'), 'index': 0, 'type': 'content_block_delta'} | 
request_id=10cec96f-60a8-4373-a7ed-3bc0ed1a9b99
2024-10-21 04:22:16 | INFO     | askgpt.app.gpt._gptclient:complete:158 | {'delta': TextDelta(text=' or', 
type='text_delta'), 'index': 0, 'type': 'content_block_delta'} | request_id=10cec96f-60a8-4373-a7ed-3bc0ed1a9b99
2024-10-21 04:22:16 | INFO     | askgpt.app.gpt._gptclient:complete:158 | {'delta': TextDelta(text=' r', type='text_delta'),
'index': 0, 'type': 'content_block_delta'} | request_id=10cec96f-60a8-4373-a7ed-3bc0ed1a9b99
2024-10-21 04:22:16 | INFO     | askgpt.app.gpt._gptclient:complete:158 | {'delta': TextDelta(text='ephrase your request,', 
type='text_delta'), 'index': 0, 'type': 'content_block_delta'} | request_id=10cec96f-60a8-4373-a7ed-3bc0ed1a9b99
2024-10-21 04:22:16 | INFO     | askgpt.app.gpt._gptclient:complete:158 | {'delta': TextDelta(text=" and I'll be", 
type='text_delta'), 'index': 0, 'type': 'content_block_delta'} | request_id=10cec96f-60a8-4373-a7ed-3bc0ed1a9b99
2024-10-21 04:22:16 | INFO     | askgpt.app.gpt._gptclient:complete:158 | {'delta': TextDelta(text=' happy to help', 
type='text_delta'), 'index': 0, 'type': 'content_block_delta'} | request_id=10cec96f-60a8-4373-a7ed-3bc0ed1a9b99
2024-10-21 04:22:16 | INFO     | askgpt.app.gpt._gptclient:complete:158 | {'delta': TextDelta(text=' you', 
type='text_delta'), 'index': 0, 'type': 'content_block_delta'} | request_id=10cec96f-60a8-4373-a7ed-3bc0ed1a9b99
2024-10-21 04:22:16 | INFO     | askgpt.app.gpt._gptclient:complete:158 | {'delta': TextDelta(text='.', type='text_delta'), 
'index': 0, 'type': 'content_block_delta'} | request_id=10cec96f-60a8-4373-a7ed-3bc0ed1a9b99
2024-10-21 04:22:16 | INFO     | askgpt.app.gpt._gptclient:complete:158 | {'index': 0, 'type': 'content_block_stop'} | 
request_id=10cec96f-60a8-4373-a7ed-3bc0ed1a9b99
2024-10-21 04:22:16 | INFO     | askgpt.app.gpt._gptclient:complete:158 | {'delta': Delta(stop_reason='end_turn', 
stop_sequence=None), 'type': 'message_delta', 'usage': MessageDeltaUsage(output_tokens=62)} | 
"""
