from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from src.app.api.model import RequestBody
from src.app.api.validation import AccessToken, parse_access_token
from src.app.gpt.model import ChatGPTRoles, CompletionModels
from src.app.gpt.service import GPTService
from src.domain.config import get_setting

gpt_router = APIRouter(prefix="/gpt")


class SendMessageRequest(RequestBody):
    question: str
    role: ChatGPTRoles
    model: CompletionModels = "gpt-3.5-turbo"


async def get_service():
    service = GPTService.build(get_setting())
    async with service.lifespan():
        yield service


@gpt_router.post("/sessions")
async def create_session(
    token: AccessToken = Depends(parse_access_token),
    service: GPTService = Depends(get_service),
):
    session_id = await service.create_session(user_id=token.sub)
    return session_id


@gpt_router.get("/sessions/{session_id}")
async def build_session(
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
