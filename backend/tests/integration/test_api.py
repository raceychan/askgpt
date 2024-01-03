import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from src.app.api.endpoints.auth import auth_settings
from src.domain.config import Settings
from src.server import app_factory


def get_test_setttings(settings: Settings):
    return settings


@pytest.fixture
def app():
    app_ = app_factory()
    app_.dependency_overrides[auth_settings] = get_test_setttings
    return app_


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
    # assert response.json() == "ok"
    # assert response.status_code == 200
