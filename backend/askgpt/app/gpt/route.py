import typing as ty

from askgpt.api.dependencies import ParsedToken, throttle_user_request
from askgpt.api.model import OK, EntityDeleted, RequestBody, Response, ResponseData
from askgpt.app.factory import GPTService, gpt_service_factory
from askgpt.app.gpt.model import ChatMessage, ChatSession
from askgpt.app.gpt.params import ChatGPTRoles
from fastapi import APIRouter, Depends
from fastapi.params import Body
from fastapi.responses import RedirectResponse, StreamingResponse
from starlette import status

gpt_router = APIRouter(prefix="/gpt")
openai_router = APIRouter(prefix="/openai")
session_router = APIRouter(prefix="/sessions")


Service = ty.Annotated[GPTService, Depends(gpt_service_factory)]


class SessionRenameRequest(RequestBody):
    name: str


class PublicSessionInfo(ResponseData):
    session_id: str
    session_name: str


class PublicChatMessage(ResponseData):
    role: ChatGPTRoles
    content: str


class PublicChatSession(ResponseData):
    user_id: str
    session_id: str
    session_name: str
    messages: list[PublicChatMessage]

    @classmethod
    def from_chat(cls, chat: ChatSession) -> ty.Self:
        return cls.model_construct(
            user_id=chat.user_id,
            session_id=chat.entity_id,
            session_name=chat.session_name,
            messages=[
                PublicChatMessage.model_construct(role=m.role, content=m.content)
                for m in chat.messages
            ],
        )


@session_router.post("", response_model=PublicChatSession)
async def create_session(service: Service, token: ParsedToken):
    # TODO: limit rate
    chat_session = await service.create_session(user_id=token.sub)

    return RedirectResponse(
        f"/v1/gpt/openai/sessions/{chat_session.entity_id}",
        status_code=status.HTTP_201_CREATED,
    )


@session_router.get("", response_model=list[PublicSessionInfo])
async def list_sessions(service: Service, token: ParsedToken):
    user_sessions = await service.list_sessions(user_id=token.sub)
    public_sessions = [
        PublicSessionInfo(session_id=ss.entity_id, session_name=ss.session_name)
        for ss in user_sessions
    ]
    return public_sessions


@session_router.get("/{session_id}")
async def get_session(
    service: Service, token: ParsedToken, session_id: str
) -> PublicChatSession:
    session = await service.get_session(user_id=token.sub, session_id=session_id)
    chat = PublicChatSession.from_chat(session)
    return chat


@session_router.put("/{session_id}")
async def rename_session(
    service: Service, token: ParsedToken, session_id: str, req: SessionRenameRequest
) -> Response:
    await service.rename_session(session_id=session_id, new_name=req.name)
    return OK


@session_router.delete("/{session_id}", status_code=204)
async def delete_session(service: Service, token: ParsedToken, session_id: str):
    await service.delete_session(session_id=session_id)
    return EntityDeleted


from openai.types.chat.completion_create_params import CompletionCreateParamsBase


@session_router.put(
    "/{session_id}",
    dependencies=[Depends(throttle_user_request)],
)
async def add_chat_message(
    service: Service,
    token: ParsedToken,
    session_id: str,
    message: ty.Annotated[ChatMessage, Body()],
    params: ty.Annotated[CompletionCreateParamsBase, Body()],
) -> StreamingResponse:
    "Create a chat message"
    if params.get("stream", False):
        stream_ans = service.chatcomplete(
            user_id=token.sub,
            session_id=session_id,
            gpt_type="openai",
            message=message,
            params=params,
        )
        return StreamingResponse(stream_ans)
    else:
        raise NotImplementedError("Not implemented")
