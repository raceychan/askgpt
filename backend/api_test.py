import asyncio

import httpx
from askgpt.domain.config import Settings, detect_settings
from tests.conftest import dft


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


async def test_get_user_info(client: httpx.AsyncClient, token: str) -> dict:
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
    print(response.json)


async def test_add_session(client: httpx.AsyncClient, token: str) -> str:
    response = await client.post(
        "/gpt/openai/sessions",
        headers={"Authorization": f"Bearer {token}"},
        follow_redirects=True,
    )
    assert response.status_code == 201
    session_id = response.headers["location"].split("/")[-1]
    return session_id


async def chat(client, access_token: str, session_id: str, *, question: str) -> str:
    data = {
        "model": "gpt-4-1106-preview",
        "question": question,
        "role": "user",
        "stream": True,
    }
    stream_io = client.stream(
        "POST",
        f"/gpt/openai/chat/{session_id}",
        json=data,
        headers={"Authorization": f"Bearer {access_token}"},
    )

    ans = ""

    async with stream_io as stream:
        async for text in stream.aiter_text():
            if not text:
                continue
            ans += text

    return ans


async def test_chat(
    client: httpx.AsyncClient, token: str, session_id: str, question: str
):
    ans = await chat(client, token, session_id, question=question)
    print(ans)
    breakpoint()


async def main():
    settings = detect_settings()
    client = client_factory(settings)
    await test_signup(client)
    token = await test_login(client)
    user = await test_get_user_info(client, token)
    await test_add_api_key(client, token)
    session_id = await test_add_session(client, token)
    await test_chat(client, token, session_id, dft.QUESTION)


if __name__ == "__main__":
    asyncio.run(main())
