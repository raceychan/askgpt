from askgpt.feat.gpt.model import UserCreated
from askgpt.domain.model.base import Event


def test_rebuild_event(user_created: UserCreated):
    data = user_created.model_dump()
    e = Event.rebuild(data)
    assert isinstance(e, UserCreated)
    assert user_created.timestamp == data["timestamp"]

    assert hash(user_created) == hash(e)
