from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from starlette import status

from src.app.api.model import RequestBody
from src.app.api.response import RedirectResponse
from src.app.api.validation import AccessToken, parse_access_token
from src.app.gpt.params import ChatGPTRoles, CompletionModels
from src.app.gpt.service import GPTService
from src.domain.config import get_setting

gpt_router = APIRouter(prefix="/gpt")


import typing as ty


class SendMessageRequest(RequestBody):
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
    stream: bool
    temperature: float | None = None
    tool_choice: ty.Any = None
    tools: list[ty.Any] | None = None
    top_p: float | None = None
    user: str | None = None
    extra_headers: ty.Mapping[str, str | ty.Literal[False]] | None
    extra_query: ty.Mapping[str, object] | None
    extra_body: object | None = None
    timeout: float | None = None


async def get_service():
    service = GPTService.from_settings(get_setting())
    async with service.lifespan():
        yield service


@gpt_router.post("/sessions")
async def create_session(
    token: AccessToken = Depends(parse_access_token),
    service: GPTService = Depends(get_service),
):
    session_id = await service.create_session(user_id=token.sub)
    return RedirectResponse(
        f"/v1/gpt/sessions/{session_id}", status_code=status.HTTP_303_SEE_OTHER
    )


@gpt_router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    token: AccessToken = Depends(parse_access_token),
    service: GPTService = Depends(get_service),
):
    session_actor = await service.get_session(user_id=token.sub, session_id=session_id)
    return session_actor.entity


@gpt_router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: str,
    req: SendMessageRequest,
    access_token: AccessToken = Depends(parse_access_token),
    service: GPTService = Depends(get_service),
):
    stream_ans = await service.stream_chat(
        user_id=access_token.sub,
        session_id=session_id,
        question=req.question,
        role=req.role,
        completion_model=req.model,
    )
    return StreamingResponse(stream_ans)  # type: ignore
