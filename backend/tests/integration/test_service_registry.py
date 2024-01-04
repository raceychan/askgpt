import pytest
from rich import print
from src.infra.service_registry import Dependency, ServiceRegistryBase


class ServiceMock:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


def servicefacotry(settings):
    return ServiceMock()


class SyncService:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class Base:
    pass

    async def lifespan(self):
        yield self


def syncfactory(settings):
    return SyncService()


def basefactory(settings):
    return Base()


def configs() -> str:
    return ""


class ServiceRegistry(ServiceRegistryBase):
    service = Dependency(ServiceMock, servicefacotry)
    sync = Dependency(SyncService, syncfactory)


@pytest.fixture(scope="module", autouse=True)
async def service_registry(settings):
    registry = ServiceRegistry(settings)

    async with registry:
        yield registry


def test_getdeps(service_registry: ServiceRegistry):
    service_registry.service
    service_registry.sync
