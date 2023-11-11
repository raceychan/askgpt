import pytest

from src.domain.model.base import DomainBase


@pytest.fixture
def domain_model():
    class TestDomain(DomainBase):
        name: str
        email: str

    dm = TestDomain(name="test", email="test@test.com")
    return dm


def test_domain_model(domain_model: DomainBase):
    domain_model.model_all_fields()

    domain_model.tableclause()
