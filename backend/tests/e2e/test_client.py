import httpx
import pytest
from src.app.api.endpoints.gpt import SendMessageRequest


@pytest.mark.skip("io")
async def test_ask_question():
    client = httpx.AsyncClient()
    url = "http://localhost:5000/v1/gpt/sessions/{session_id}/messages"

    req = SendMessageRequest(
        question="what is the meaning of life?", role="user", model="gpt-3.5-turbo"
    )
    data = req.model_dump()
    url = url.format(session_id=test_data["session_id"])

    headers = dict(Authorization=f"Bearer {test_data['token']}")

    async with client.stream(
        method="post", headers=headers, url=url, json=data
    ) as resp:
        async for chunk in resp.aiter_text():
            print(chunk, end="")
