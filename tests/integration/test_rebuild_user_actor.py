# import pytest

# from src.app.gpt import model, service

# # from src.app.gpt.model import User
# from src.domain.config import TestDefaults


# @pytest.fixture(scope="module")
# def send_chat_message():
#     return service.SendChatMessage(
#         user_id=TestDefaults.USER_ID,
#         session_id=TestDefaults.SESSION_ID,
#         user_message="hello",
#     )


# @pytest.fixture(scope="module")
# def user_actor():
#     user = model.User(user_id=TestDefaults.USER_ID)
#     return service.UserActor(user=user)


# @pytest.fixture(scope="module")
# def session_actor():
#     user = model.User(user_id=TestDefaults.user_id)
#     return service.UserActor(user=user)


# def test_rebuild_user_from_events():
#     ...
