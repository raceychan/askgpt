import typing as ty

from fastapi import APIRouter, Body, Depends
from fastapi.responses import RedirectResponse, StreamingResponse
from starlette import status

from askgpt.api.errors import QuotaExceededError
from askgpt.api.model import EmptyResponse, RequestBody, Response, ResponseData
from askgpt.api.throttler import UserRequestThrottler
from askgpt.app.auth.api import ParsedToken
from askgpt.app.gpt.service import GPTService
from askgpt.app.gpt_factory import SessionService, dynamic_gpt_service_resolver
from askgpt.domain.config import dg

from ._model import ChatSession
from .anthropic._params import AnthropicChatMessageOptions
from .openai._params import ChatGPTRoles, OpenAIChatMessageOptions

gpt_router = APIRouter(prefix="/gpt")
sessions = APIRouter(prefix="/sessions")

DSessionService = ty.Annotated[SessionService, Depends(dg.factory(SessionService))]
DGPTService = ty.Annotated[GPTService, Depends(dynamic_gpt_service_resolver)]


async def throttle_user_request(
    access_token: ParsedToken,
):
    throttler = dg.resolve(UserRequestThrottler)
    wait_time = await throttler.validate(access_token.sub)
    if wait_time:
        raise QuotaExceededError(throttler.max_tokens, wait_time)


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


@gpt_router.post("/sessions", response_model=PublicChatSession)
async def create_session(service: DSessionService, token: ParsedToken):
    # TODO: 1. limit rate 2. require idem id to avoid creating multiple sessions accidentally
    chat_session = await service.create_session(user_id=token.sub)

    return RedirectResponse(
        f"/v1/gpt/openai/sessions/{chat_session.entity_id}",
        status_code=status.HTTP_201_CREATED,
    )


@gpt_router.get("/sessions", response_model=list[PublicSessionInfo])
async def list_sessions(service: DSessionService, token: ParsedToken):
    user_sessions = await service.list_sessions(user_id=token.sub)
    public_sessions = [
        PublicSessionInfo(session_id=ss.entity_id, session_name=ss.session_name)
        for ss in user_sessions
    ]
    return public_sessions


@sessions.get("/{session_id}")
async def get_session(
    service: DSessionService, token: ParsedToken, session_id: str
) -> PublicChatSession:
    session = await service.get_session(user_id=token.sub, session_id=session_id)
    chat = PublicChatSession.from_chat(session)
    return chat


@sessions.put("/{session_id}")
async def rename_session(
    service: DSessionService,
    token: ParsedToken,
    session_id: str,
    req: SessionRenameRequest,
) -> Response:
    await service.rename_session(session_id=session_id, new_name=req.name)
    return EmptyResponse.OK


@sessions.delete("/{session_id}", status_code=204)
async def delete_session(service: DSessionService, token: ParsedToken, session_id: str):
    await service.delete_session(session_id=session_id)
    return EmptyResponse.EntityDeleted


# async def validate_params(
#     gpt_type: str = Query(...),
#     params: OpenAIChatMessageOptions | AnthropicChatMessageOptions = Body(),
# ):
#     if gpt_type == "openai":
#         return OpenAIChatMessageOptions(**params)
#     elif gpt_type == "anthropic":
#         return AnthropicChatMessageOptions(**params)
#     else:
#         raise ValueError("Invalid query parameter value")


@sessions.post(
    "/{session_id}/messages",
    dependencies=[Depends(throttle_user_request)],
)
async def add_chat_message(
    token: ParsedToken,
    service: DGPTService,
    session_id: str,
    params: AnthropicChatMessageOptions | OpenAIChatMessageOptions = Body(),
) -> StreamingResponse:
    "Create a chat message"
    stream = params.pop("stream", True)

    if stream:
        stream_ans = service.chatcomplete(
            user_id=token.sub,
            session_id=session_id,
            params=params,
        )
        return StreamingResponse(stream_ans)
    else:
        raise NotImplementedError("Not implemented")
