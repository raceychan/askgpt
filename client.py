from __future__ import annotations

import dotenv
import httpx
from rich.console import Console
from rich.markdown import Markdown

console = Console()

configs: dict[str, str] = dotenv.dotenv_values("credentials.env")  # type: ignore


def client_factory() -> httpx.AsyncClient:
    remote_host, remote_port, remote_path = (
        configs["REMOTE_HOST"],
        configs["REMOTE_PORT"],
        configs["API_PATH"],
    )
    URL = f"http://{remote_host}:{remote_port}{remote_path}"
    return httpx.AsyncClient(base_url=URL)


async def login(client: httpx.AsyncClient) -> str:
    username, password = configs["USER_NAME"], configs["USER_PASSWORD"]
    data = {"username": username, "password": password}
    response = await client.post("/auth/login", data=data, follow_redirects=True)
    return response.json()["access_token"]


async def chat(
    client: httpx.AsyncClient, access_token: str, session_id: str, *, question: str
) -> str:
    data = {
        "model": "gpt-4-1106-preview",
        "question": "enter your question here",
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


from rich import prompt


async def make_request():
    client = client_factory()
    access_token = await login(client)
    session_id: str = configs["SESSION_ID"]

    question = prompt.Prompt.ask("Enter your question here:")
    if not question:
        return
    await chat(client, access_token, session_id, question=question)


if __name__ == "__main__":
    import asyncio

    asyncio.run(make_request())
