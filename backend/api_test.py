import asyncio

import httpx
import orjson
from askgpt.domain.config import Settings, detect_settings
from rich import print
from tests.conftest import dft


def client_factory(settings: Settings) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=f"http://{settings.api.HOST}:{settings.api.PORT}/v{settings.api.API_VERSION}",
        timeout=30,
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
    data = {"api_key": "test", "api_type": "openai", "key_name": "test"}
    response = await client.post(
        "/auth/apikeys", headers={"Authorization": f"Bearer {token}"}, json=data
    )
    assert response.status_code in (201, 401, 409), response.status_code


async def test_add_session(client: httpx.AsyncClient, token: str) -> str:
    response = await client.post(
        "/gpt/sessions",
        headers={"Authorization": f"Bearer {token}"},
        follow_redirects=True,
    )
    assert response.status_code == 201
    session_id = response.headers["location"].split("/")[-1]
    return session_id


async def chat(
    client: httpx.AsyncClient, access_token: str, session_id: str, *, question: str
) -> str:
    data = {
        "model": "gpt-4-1106-preview",
        "message": {
            "role": "user",
            "content": question,
        },
        "stream": True,
        # "name": "hi",
    }

    stream_io = client.stream(
        "POST",
        f"/gpt/openai/sessions/{session_id}/messages",
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
    if ans:
        print(orjson.loads(ans))
    else:
        print(ans)


async def main():
    settings = detect_settings()
    client = client_factory(settings)
    await test_signup(client)
    token = await test_login(client)
    user = await test_get_user_info(client, token)
    await test_add_api_key(client, token)
    session_id = await test_add_session(client, token)
    await test_chat(client, token, session_id, dft.QUESTION)


# async def test_openai_api():
#     from openai import AsyncOpenAI

#     settings = detect_settings()
#     # client = AsyncOpenAI(api_key=settings.openai_api_key)
#     client = AsyncOpenAI(api_key="sk-proj-123")
#     resp = await client.chat.completions.create(
#         model="gpt-4o",
#         messages=[{"role": "user", "content": "hi"}],
#         max_tokens=10,
#         stream=True,
#     )
#     async for chunk in resp:
#         print(chunk)


if __name__ == "__main__":
    asyncio.run(main())
    # asyncio.run(test_openai_api())
