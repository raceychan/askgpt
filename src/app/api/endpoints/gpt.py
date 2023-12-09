from fastapi import APIRouter, Depends

from src.app.api.validator import AccessToken, parse_access_token
from src.app.gpt.service import GPTService
from src.domain.config import get_setting
from src.app.gpt.model import ChatMessage

gpt_router = APIRouter(prefix="/gpt")


async def get_service():
    service = GPTService.build(get_setting())
    async with service.lifespan():
        yield service

@gpt_router.post("/sessions")
async def ask(
    token: AccessToken = Depends(parse_access_token),
    service: GPTService = Depends(get_service),
):
    await service.user_create_session()


@gpt_router.get("/sessions/{session_id}")
async def ask(
    session_id: str,
    question: str,
    token: AccessToken = Depends(parse_access_token),
    service: GPTService = Depends(get_service),
):
    await service.send_question(
        user_id=token.sub, session_id=session_id, question=question
    )
