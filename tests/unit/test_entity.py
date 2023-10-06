# from src.domain.model import Entity, Field
from src.app.service.gpt import User, UserCredated


def test_create_user_from_event():
    e = UserCredated(user_id="123")
    u = User.apply(e)
    assert isinstance(u, User)
    assert u.entity_id == e.entity_id
