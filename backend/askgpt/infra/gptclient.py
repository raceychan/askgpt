import abc
import typing as ty

import httpx
import openai
from openai.types import beta as openai_beta
from openai.types import chat as openai_chat
from askgpt.app.gpt import model, params
from askgpt.domain.base import SupportedGPTs
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


class GPTClient(abc.ABC):
    async def complete(
        self,
        messages: list[model.ChatMessage],
        model: model.CompletionModels,
        options: params.CompletionOptions,  # type: ignore
    ) -> (
        ty.AsyncIterable[openai_chat.ChatCompletionChunk] | openai_chat.ChatCompletion
    ): ...

    @classmethod
    @abc.abstractmethod
    def from_apikey(cls, api_key: str) -> ty.Self: ...


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
        options: params.CompletionOptions,  # type: ignore
    ) -> ty.AsyncIterable[openai_chat.ChatCompletionChunk] | openai_chat.ChatCompletion:
        msgs = self.message_adapter(messages)
        resp: ty.AsyncIterable[openai_chat.ChatCompletionChunk] = (
            await self._client.chat.completions.create(
                messages=msgs,  # type: ignore
                model=model,
                **options,
            )
        )

        return resp

    def message_adapter(
        self, messages: list[model.ChatMessage]
    ) -> list[dict[str, ty.Any]]:
        return [message.asdict(exclude={"user_id"}) for message in messages]

    @classmethod
    @lru_cache(maxsize=1000)
    def from_apikey(cls, api_key: str) -> "OpenAIClient":
        return cls.build(api_key=api_key, timeout=30.0)

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
