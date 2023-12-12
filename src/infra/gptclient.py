import typing as ty

from openai import AsyncOpenAI
from openai.types.beta import Thread
from openai.types.beta.assistant import Assistant
from openai.types.chat import ChatCompletionChunk

from src.app.gpt import model, params


class APIPool:
    # https://medium.com/@colemanhindes/unofficial-gpt-3-developer-faq-fcb770710f42
    # How many concurrent requests can I make to the API?:
    # Only 2 concurrent requests can be made per API key at a time.
    ...


class AIClient(ty.Protocol):
    async def send_chat(self, message: model.ChatMessage) -> ty.Any:
        ...


class OpenAIClient:
    def __init__(self, client: AsyncOpenAI):
        self._client = client

    async def assistant(
        self, model: str, name: str, instructions: str, tools: list[str]
    ) -> Assistant:
        return await self._client.beta.assistants.create(model=model)

    async def create_thread(self) -> Thread:
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
        **options: ty.Unpack[params.CompletionOptions],
    ) -> ty.AsyncGenerator[ChatCompletionChunk, None]:
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
    def from_apikey(cls, api_key: str) -> ty.Self:
        client = AsyncOpenAI(api_key=api_key)
        return cls(client=client)
