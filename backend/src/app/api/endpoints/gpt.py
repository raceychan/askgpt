import typing as ty

from fastapi import APIRouter, Depends
from src.app.api.dependencies import (
    AccessToken,
    parse_access_token,
    throttle_user_request,
)
from src.app.api.model import RequestBody
from src.app.api.response import RedirectResponse, StreamingResponse
from src.app.factory import ApplicationServices
from src.app.gpt.params import ChatGPTRoles, CompletionModels
from starlette import status

gpt_router = APIRouter(prefix="/gpt")
llm_router = APIRouter(prefix="/llm")
openai_router = APIRouter(prefix="/openai")


class ChatCompletionRequest(RequestBody):
    "This is problematic, in openapi test there are a lot of bad defaults here."
    question: str
    role: ChatGPTRoles
    model: CompletionModels = "gpt-3.5-turbo"
    frequency_penalty: float | None = None
    function_call: ty.Any = None
    functions: list[ty.Any] | None = None
    logit_bias: dict[str, int] | None = None
    max_tokens: int | None = None
    n: int | None = None
    presence_penalty: float | None = None
    response_format: ty.Any = None
    seed: int | None = None
    stop: str | None | list[str] = None
    stream: bool | None = None
    temperature: float | None = None
    tool_choice: ty.Any = None
    tools: list[ty.Any] | None = None
    top_p: float | None = None
    user: str | None = None
    extra_headers: ty.Mapping[str, str | ty.Literal[False]] | None = None
    extra_query: ty.Mapping[str, object] | None = None
    extra_body: dict | None = None
    timeout: float | None = None


class PulibcSessionInfo(ty.TypedDict):
    session_id: str
    session_name: str


class SessionRenameRequest(RequestBody):
    name: str


@openai_router.post("/sessions")
async def create_session(
    token: AccessToken = Depends(parse_access_token),
):
    # TODO: limit rate
    chat_session = await ApplicationServices.gpt_service.create_session(
        user_id=token.sub
    )

    return RedirectResponse(
        f"/v1/gpt/openai/sessions/{chat_session.entity_id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@openai_router.get("/sessions", response_model=list[PulibcSessionInfo])
async def list_sessions(
    token: AccessToken = Depends(parse_access_token),
):
    user_sessions = await ApplicationServices.gpt_service.list_sessions(
        user_id=token.sub
    )
    public_sessions = [
        PulibcSessionInfo(session_id=ss.entity_id, session_name=ss.session_name)
        for ss in user_sessions
    ]
    return public_sessions


@openai_router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    token: AccessToken = Depends(parse_access_token),
):
    session_actor = await ApplicationServices.gpt_service.get_session_actor(
        user_id=token.sub, session_id=session_id
    )
    return session_actor.entity


@openai_router.put("/sessions/{session_id}")
async def rename_session(
    session_id: str,
    req: SessionRenameRequest,
    token: AccessToken = Depends(parse_access_token),
):
    await ApplicationServices.gpt_service.rename_session(
        session_id=session_id, new_name=req.name
    )


@openai_router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    token: AccessToken = Depends(parse_access_token),
):
    await ApplicationServices.gpt_service.delete_session(session_id=session_id)


@openai_router.post("/chat/{session_id}", dependencies=[Depends(throttle_user_request)])
async def chat(
    session_id: str,
    req: ChatCompletionRequest,
    access_token: AccessToken = Depends(parse_access_token),
):
    data = req.model_dump(exclude_unset=True)
    data.setdefault("user", access_token.sub)

    stream_ans = await ApplicationServices.gpt_service.stream_chat(
        user_id=access_token.sub,
        session_id=session_id,
        gpt_type="openai",
        role=data.pop("role"),
        question=data.pop("question"),
        options=data,
    )
    return StreamingResponse(stream_ans)  # type: ignore
