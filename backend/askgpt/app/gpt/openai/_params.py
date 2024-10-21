import typing as ty

from askgpt.domain.model.base import ValueObject
from openai.types import ChatModel as CompletionModels
from openai.types.chat import ChatCompletionChunk
from openai.types.chat import ChatCompletionMessageParam as ChatCompletionMessageParam
from openai.types.chat import (
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionToolParam,
    completion_create_params,
)
from openai.types.chat.completion_create_params import (
    CompletionCreateParams as CompletionCreateParams,
)
from openai.types.chat.completion_create_params import (
    CompletionCreateParamsBase as CompletionCreateParamsBase,
)
from openai.types.chat.completion_create_params import (
    CompletionCreateParamsStreaming as CompletionCreateParamsStreaming,
)

type ChatGPTRoles = ty.Literal["system", "user", "assistant", "function"]


class CompletionMessage(ty.TypedDict, total=False):
    role: ty.Required[ChatGPTRoles]
    content: ty.Required[str]
    name: str | None


class OpenAIChatMessageOptions(CompletionCreateParamsBase, total=False):
    message: ty.Required[CompletionMessage]
    model: ty.Required[CompletionModels]
    frequency_penalty: float | None
    function_call: completion_create_params.FunctionCall
    functions: list[completion_create_params.Function]
    logit_bias: dict[str, int] | None
    max_tokens: int | None
    n: int | None
    presence_penalty: float | None
    response_format: completion_create_params.ResponseFormat
    seed: int | None
    stop: (str | None) | list[str]
    stream: bool
    temperature: float | None
    tool_choice: ChatCompletionToolChoiceOptionParam
    tools: list[ChatCompletionToolParam]
    top_p: float | None
    user: str
    extra_headers: ty.Any | None
    extra_query: ty.Any | None
    extra_body: ty.Any | None
    timeout: float | None


class CompleteMessage(ty.TypedDict):
    role: ChatGPTRoles
    content: str


class ChatResponse(ValueObject):
    """
    a domain representation of chat response
    """

    chunk: ChatCompletionChunk

    async def __aiter__(self) -> ty.Any: ...
