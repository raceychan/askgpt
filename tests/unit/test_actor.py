import pytest

from src.app.gpt.service import GPTSystem
from src.app.gpt.user import CreateSession, CreateUser, SendChatMessage
from src.domain.config import TestDefaults


@pytest.fixture(scope="module")
def create_user():
    return CreateUser(user_id="admin")


async def test_create_user(create_user: CreateUser):
    system = GPTSystem()
    await system.handle(create_user)
