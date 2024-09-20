import httpx
from askgpt.domain.config import get_setting
import sysconfig




def client_factory() -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url="http://192.168.50.22:5000")


async def login(test_client: httpx.AsyncClient) -> str:
    data = {"username": "test@email.com", "password": "test"}
    response = await test_client.post("/auth/login", data=data, follow_redirects=True)
    assert response.status_code == 200
    return response.json()["access_token"]


async def main():
    settings = get_setting("setitngs.toml")


if __name__ == "__main__":
    breakpoint()
