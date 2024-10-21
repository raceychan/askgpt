import typing as ty

from anthropic.types.message_create_params import MessageCreateParamsStreaming
from anthropic.types.message_param import MessageParam

# from anthropic.types.metadata_param import MetadataParam
# from anthropic.types.model_param import ModelParam
# from anthropic.types.text_block_param import TextBlockParam
# from anthropic.types.tool_choice_param import ToolChoiceParam
from anthropic.types.tool_param import ToolParam


class AnthropicChatMessageOptions(MessageCreateParamsStreaming, total=False):
    messages: ty.Required[list[MessageParam]]
    system: str
    tools: list[ToolParam]
