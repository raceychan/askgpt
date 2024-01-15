import typing as ty

from openai._types import Body, Headers, Query
from openai.types.chat import (
    ChatCompletionChunk,
    ChatCompletionMessageParam,
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionToolParam,
    completion_create_params,
)
from openai.types.chat.completion_create_params import (
    CompletionCreateParams as CompletionCreateParams,
)
from openai.types.chat.completion_create_params import (
    CompletionCreateParamsStreaming as CompletionCreateParamsStreaming,
)

from src.domain.model.base import ValueObject

# TODO: read
# https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/domain-events-design-implementation


# class ModelEndpoint(BaseModel):
#     endpoint: Path
#     models: tuple[str, ...]


# class CompletionEndPoint(ModelEndpoint):
#     endpoint: Path = Path("/v1/chat/completion")
#     model: CompletionModels

CompletionModels = ty.Literal[
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-0613",
    "gpt-3.5-turbo-16k",
    "gpt-3.5-turbo-16k-0613",
    "gpt-4",
    "gpt-4-0613",
    "gpt-4-32k",
    "gpt-4-32k-0613",
]

# TODO: use enum
ChatGPTRoles = ty.Literal["system", "user", "assistant", "function"]


class CompletionOptions(ty.TypedDict, total=False):
    messages: ty.List[ChatCompletionMessageParam]
    model: CompletionModels
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
    extra_headers: Headers | None
    extra_query: Query | None
    extra_body: Body | None
    timeout: float | None


class ChatResponse(ValueObject):
    """
    a domain representation of chat response
    """

    chunk: ChatCompletionChunk

    async def __aiter__(self) -> ty.Any:
        ...
