import asyncio

import httpx
from tests.conftest import dft

from askgpt.domain.config import Settings, detect_settings


def client_factory(settings: Settings) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=f"http://{settings.api.HOST}:{settings.api.PORT}/v{settings.api.API_VERSION}"
    )


async def test_signup(client: httpx.AsyncClient) -> str:
    data = {"email": dft.USER_EMAIL, "password": dft.USER_PASSWORD}
    response = await client.post("/auth/signup", json=data, follow_redirects=True)
    assert response.status_code in (200, 409)
    return response.json()


async def test_login(test_client: httpx.AsyncClient) -> str:
    data = {"username": dft.USER_EMAIL, "password": dft.USER_PASSWORD}
    response = await test_client.post("/auth/login", data=data, follow_redirects=True)
    assert response.status_code == 200
    return response.json()["access_token"]


async def test_get_user(client: httpx.AsyncClient, token: str) -> dict:
    response = await client.get(
        "/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    return response.json()


async def test_add_api_key(client: httpx.AsyncClient, token: str) -> None:
    data = {"api_key": "test", "api_type": "openai"}
    response = await client.post(
        "/auth/apikeys", json=data, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200


async def main():
    settings = detect_settings()
    client = client_factory(settings)
    await test_signup(client)
    token = await test_login(client)
    user = await test_get_user(client, token)
    await test_add_api_key(client, token)


if __name__ == "__main__":
    asyncio.run(main())
