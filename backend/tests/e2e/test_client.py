import httpx
import pytest
from fastapi import FastAPI
from tests._const import dft


async def test_openapi(app: FastAPI):
    return app.openapi()


@pytest.mark.skip("io")
async def test_ask_question(client: httpx.AsyncClient, session_id: str, token: str):
    url = "/gpt/sessions/{session_id}/messages"

    req = dict(
        question="what is the meaning of life?", role="user", model="gpt-3.5-turbo"
    )  # type: ignore
    url = url.format(session_id=session_id)

    headers = dict(Authorization=f"Bearer {token}")

    async with client.stream(method="post", headers=headers, url=url, json=req) as resp:
        async for chunk in resp.aiter_text():
            print(chunk, end="")


def test_read_main(client: httpx.Client):
    response = client.get("/health")
    assert response.status_code == 200


# def test_signup_user(client: httpx.Client):
#     data = dict(username=dft.USER_EMAIL, password=dft.USER_PASSWORD)
#     resp = client.post("/auth/login", data=data)
