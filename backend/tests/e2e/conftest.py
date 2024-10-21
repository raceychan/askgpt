import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from askgpt.api.app import app_factory
from askgpt.domain.config import Settings


@pytest.fixture(scope="package")
async def app(settings: Settings):
    return app_factory(settings=settings)


@pytest.fixture(scope="module")
async def client(app: FastAPI):
    return TestClient(app=app, base_url="http://testserver/v1")
