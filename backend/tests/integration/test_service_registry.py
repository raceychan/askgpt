import pytest
from rich import print
from src.app.service_registry import Dependency, ServiceRegistryBase


class ServiceMock:
    async def __aenter__(self):
        print("\n service enter")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print("\n service exit")
        pass


def servicefacotry(settings):
    print("received", settings)
    return ServiceMock()


class SyncService:
    def __enter__(self):
        print("\n base enter")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("\n base exit")
        pass


class Base:
    pass


def syncfactory(settings):
    return SyncService()


def basefactory(settings):
    return Base()


def configs() -> str:
    return ""


class ServiceRegistry(ServiceRegistryBase):
    service = Dependency(ServiceMock, servicefacotry)
    sync = Dependency(SyncService, syncfactory)
    base = Dependency(Base, basefactory)


@pytest.fixture(scope="module", autouse=True)
async def service_registry(settings):
    async with ServiceRegistry(settings) as registry:
        yield registry
    ...


def test_getdeps(service_registry: ServiceRegistry):
    service_registry.service
    service_registry.sync
    service_registry.base
