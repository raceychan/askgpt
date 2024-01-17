import dotenv
import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from src.app.gpt.gptclient import ClientRegistry
from src.domain.config import Settings
from src.server import app_factory  # type: ignore
from src.toolkit.fileutil import fileutil


@pytest.fixture
async def api_key() -> str:
    f = fileutil.find("test.env")
    test_secret: dict[str, str] = dotenv.dotenv_values(f)
    return test_secret["OPENAI_API_KEY"]


async def signup(test_client: AsyncClient) -> None:
    data = {"email": "test@email.com", "password": "test"}
    response = await test_client.post("/auth/signup", json=data, follow_redirects=True)
    assert response.status_code == 200
    user_id = response.json()["user_id"]
    return user_id


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


async def test_add_api_key(
    test_client: AsyncClient, auth_header: dict[str, str], api_key: str
):
    response = await test_client.post(
        "/users/apikeys",
        headers=auth_header,
        json=dict(api_type="openai", api_key=api_key),
    )
    assert response.status_code == 200


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
    ClientRegistry.register("openai")(ClientRegistry.client_factory("test"))
    session_id: str = await create_session(test_client, auth_header)
    question = "ping"
    ans = ""
    async with test_client.stream(
        "POST",
        f"/gpt/openai/chat/{session_id}",
        json=dict(question=question, role="user", model="gpt-3.5-turbo"),
        headers=auth_header,
    ) as r:
        async for line in r.aiter_lines():
            ans += line

    assert ans == "pong"


async def test_list_sessions(test_client: AsyncClient, auth_header: dict[str, str]):
    response = await test_client.get(
        "/gpt/openai/sessions", headers=auth_header, follow_redirects=True
    )
    assert response.status_code == 200
    session_info = response.json()
    assert session_info
