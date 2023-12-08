from fastapi import APIRouter, Depends

from src.app.gpt.service import GPTService
from src.domain.config import get_setting

gpt = APIRouter(prefix="/gpt")


async def get_service():
    service = GPTService.build(get_setting())
    async with service.setup_system():
        yield service


@gpt.get("/{question}")
async def ask(
    question: str,
    user_id: str,
    session_id: str,
    service: GPTService = Depends(get_service),
):
    # TODO: use token to validate
    auth = service.auth(user_id)
    await service.send_question(auth, question, session_id)


from sqlalchemy.pool import NullPool
