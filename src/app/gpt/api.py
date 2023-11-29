from fastapi import APIRouter, Depends

from src.app.auth.auth import Authenticator
from src.app.gpt.factory import get_setting
from src.app.gpt.service import GPTService

gpt_router = APIRouter(prefix="/gpt")


async def get_service():
    service = GPTService.build(get_setting())
    async with service.setup_system():
        yield service


@gpt_router.get("/{question}")
async def ask(
    question: str,
    user_id: str,
    session_id: str,
    service: GPTService = Depends(get_service),
):
    auth = Authenticator(user_id)
    await service.send_question(auth, question, session_id)
