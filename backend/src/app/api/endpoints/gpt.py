import typing as ty

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from starlette import status

from src.app.api.dependencies import (
    AccessToken,
    parse_access_token,
    throttle_user_request,
)
from src.app.api.model import RequestBody
from src.app.api.response import RedirectResponse
from src.app.factory import ApplicationServices
from src.app.gpt.params import ChatGPTRoles, CompletionModels

gpt_router = APIRouter(prefix="/gpt")
llm_router = APIRouter(prefix="/llm")
openai = APIRouter(prefix="/openai")


class ChatCompletionRequest(RequestBody):
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
    extra_body: object | None = None
    timeout: float | None = None


@openai.post("/sessions")
async def create_session(
    token: AccessToken = Depends(parse_access_token),
):
    session_id = await ApplicationServices.gpt_service.create_session(user_id=token.sub)

    return RedirectResponse(
        f"/v1/gpt/openai/sessions/{session_id}", status_code=status.HTTP_303_SEE_OTHER
    )


@openai.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    token: AccessToken = Depends(parse_access_token),
):
    session_actor = await ApplicationServices.gpt_service.get_session(
        user_id=token.sub, session_id=session_id
    )
    return session_actor.entity


@openai.post("/chat/{session_id}", dependencies=[Depends(throttle_user_request)])
async def chat(
    session_id: str,
    req: ChatCompletionRequest,
    access_token: AccessToken = Depends(parse_access_token),
):
    data = req.model_dump(exclude_unset=True)

    stream_ans = await ApplicationServices.gpt_service.stream_chat(
        user_id=access_token.sub,
        session_id=session_id,
        gpt_type="openai",
        role=data.pop("role"),
        question=data.pop("question"),
        options=data,
    )
    return StreamingResponse(stream_ans)  # type: ignore
