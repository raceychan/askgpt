import pytest
from pydantic import computed_field

from askgpt.domain.model.base import DomainModel


@pytest.fixture
def domain_model():
    class TestDomain(DomainModel):
        name: str
        email: str

        @computed_field
        def full_name(self) -> str:
            return f"{self.name}+{self.email}"

    dm = TestDomain(name="test", email="test@test.com")
    return dm


def test_domain_model(domain_model: DomainModel):
    fields = domain_model.model_all_fields()
    assert fields == {"full_name": str, "name": str, "email": str}
    tc = domain_model.tableclause()
    assert len(tc.c) == len(fields)
