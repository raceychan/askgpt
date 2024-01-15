import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from src.domain.config import Settings
from src.server import app_factory # type: ignore

import dotenv

dotenv.dotenv_values()


async def signup(test_client: AsyncClient) -> None:
    data = {"email": "test@email.com", "password": "test"}
    response = await test_client.post("/auth/signup", json=data, follow_redirects=True)
    assert response.status_code == 200


async def login(test_client: AsyncClient) -> str:
    data = {"username": "test@email.com", "password": "test"}
    response = await test_client.post("/auth/login", data=data, follow_redirects=True)
    assert response.status_code == 200
    return response.json()["access_token"]


async def create_session(test_client: AsyncClient, auth_header: dict[str, str]):
    response = await test_client.post(
        f"/gpt/openai/sessions", headers=auth_header, follow_redirects=True
    )
    assert response.status_code == 200
    session_id = response.json()["session_id"]
    return session_id


@pytest.fixture(scope="module")
async def app(settings: Settings):
    app_ = app_factory(settings=settings)
    async with app_.router.lifespan_context(settings):  # type: ignore
        yield app_


@pytest.fixture(scope="module")
async def test_client(app: FastAPI):
    client = AsyncClient(app=app, base_url=f"http://testserver/v{app.version}")

    async with client as client:
        yield client


@pytest.fixture(scope="module")
async def auth_header(test_client: AsyncClient):
    await signup(test_client)
    token = await login(test_client)
    return {"Authorization": f"Bearer {token}"}


async def test_heal(test_client: AsyncClient):
    response = await test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == "ok"


async def test_find_user(test_client: AsyncClient):
    response = await test_client.get(f"/users/", params={"email": "nonexist"})
    res_json = response.json()
    assert res_json["detail"]["error_code"] == "UserNotFoundError"
    assert response.status_code == 404


async def test_gpt_chat(test_client: AsyncClient, auth_header: dict[str, str]):
    session_id: str = await create_session(test_client, auth_header)
    response = await test_client.post(
        f"/gpt/openai/chat/{session_id}",
        json=dict(question="test", role="user", model="gpt-3.5-turbo"),
        headers=auth_header,
    )
    if not response.status_code == 200:
        print(response.text)
