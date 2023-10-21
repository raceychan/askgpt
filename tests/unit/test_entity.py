from src.app.gpt.user import User, UserCreated


def test_create_user_from_event():
    e = UserCreated(user_id="123")
    u = User.apply(e)
    assert isinstance(u, User)
    assert u.entity_id == e.entity_id
