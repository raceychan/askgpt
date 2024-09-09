from __future__ import annotations

import dotenv
import httpx
from rich.console import Console
from rich.markdown import Markdown
from rich import prompt

console = Console()

configs: dict[str, str] = dotenv.dotenv_values("credentials.env")  # type: ignore


def client_factory() -> httpx.AsyncClient:
    remote_host, remote_port, remote_path = (
        configs.get("REMOTE_HOST", "0.0.0.0"),
        configs.get("REMOTE_PORT", 5000),
        configs.get("API_PATH", "/v1"),
    )
    URL = f"http://{remote_host}:{remote_port}{remote_path}"
    return httpx.AsyncClient(base_url=URL)

class GPTClient:
    def __init__(self, client: httpx.AsyncClient, credentials: dict[str, str]):
        self._client = client
        self._credentials = credentials

    async def login(self, username: str ="", password:str="") -> str:
        username, password = self._credentials.values() or (username, password)
        data = {"username": username, "password": password}
        response = await self._client.post("/auth/login", data=data, follow_redirects=True)
        return response.json()["access_token"]


    async def chat(
        self, access_token: str, session_id: str, *, question: str
    ) -> str:
        data = {
            "model": "gpt-4-1106-preview",
            "question": "enter your question here",
            "role": "user",
            "stream": True,
        }
        stream_io = self._client.stream(
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




async def make_request():
    httpx_client = client_factory()
    credentials = dict(username=configs.get("username", ""), password=configs.get("password", ""))
    gpt_client = GPTClient(httpx_client, credentials)
    
    access_token = await gpt_client.login()
    session_id: str = configs["SESSION_ID"]

    question = prompt.Prompt.ask("Enter your question here:")
    if not question:
        return
    await gpt_client.chat(access_token, session_id, question=question)


if __name__ == "__main__":
    import asyncio

    asyncio.run(make_request())
