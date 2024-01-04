import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from src.domain.config import Settings
from src.server import app_factory


@pytest.fixture(scope="module")
async def app(settings: Settings):
    app_ = app_factory()
    async with app_.router.lifespan_context(settings):
        yield app_


@pytest.fixture
async def test_client(app: FastAPI):
    client = AsyncClient(app=app, base_url=f"http://testserver/v{app.version}")

    async with client as client:
        yield client


async def test_heal(test_client: AsyncClient):
    response = await test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == "ok"


async def test_gpt(test_client: AsyncClient):
    response = await test_client.get(f"/users/", params={"email": "test"})
    res_json = response.json()
    assert res_json["detail"]["error_code"] == "UserNotFoundError"
    assert response.status_code == 404
