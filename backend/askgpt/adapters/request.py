import httpx


def client_factory():
    return httpx.AsyncClient()
