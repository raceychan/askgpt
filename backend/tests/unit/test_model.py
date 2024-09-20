import pytest

from askgpt.domain.model.base import DomainModel


@pytest.fixture
def domain_model():
    class TestDomain(DomainModel):
        name: str
        email: str

    dm = TestDomain(name="test", email="test@test.com")
    return dm


def test_domain_model(domain_model: DomainModel):
    domain_model.model_all_fields()
    domain_model.tableclause()
