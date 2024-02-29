from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class CompletionRequest(_message.Message):
    __slots__ = ("question",)
    QUESTION_FIELD_NUMBER: _ClassVar[int]
    question: str
    def __init__(self, question: _Optional[str] = ...) -> None: ...

class CompletionResponse(_message.Message):
    __slots__ = ("completion",)
    COMPLETION_FIELD_NUMBER: _ClassVar[int]
    completion: str
    def __init__(self, completion: _Optional[str] = ...) -> None: ...
