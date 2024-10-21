# import typing as ty

# import pytest
# from tests.conftest import dft

# from askgpt.adapters.cache import Cache, MemoryCache
# from askgpt.adapters.queue import BaseProducer, QueueBroker
# from askgpt.domain import config
# from askgpt.app.actor import QueueBox
# from askgpt.app.gpt import model, service
# from askgpt.infra import factory
# from askgpt.infra.eventstore import EventStore
# from askgpt.infra.gptclient import OpenAIClient


# @pytest.fixture(scope="module")
# def chat_messages():
#     return [
#         model.ChatMessage.as_prompt(content="answer me seriously!"),
#         model.ChatMessage.as_user(content="ping"),
#         model.ChatMessage.as_assistant(content="pong"),
#         model.ChatMessage.as_user(content="ask"),
#         model.ChatMessage.as_assistant(content="answer"),
#     ]


# @pytest.fixture(scope="module")
# async def gptsystem(
#     settings: config.Settings,
#     eventstore: EventStore,
#     cache: Cache[str, ty.Any],
# ):
#     system = service.GPTSystem(
#         boxfactory=QueueBox,
#         ref=settings.actor_refs.SYSTEM,
#         settings=settings,
#         producer=BaseProducer(QueueBroker(100)),
#         event_store=eventstore,
#         cache=MemoryCache(),
#     )
#     await system.start()
#     return system


# @pytest.fixture(scope="module")
# async def user_actor(gptsystem: service.GPTSystem):
#     cmd = model.CreateUser(user_id=dft.USER_ID)
#     user = await gptsystem.create_user(cmd)
#     return user


# @pytest.fixture(scope="module")
# async def session_actor(user_actor: service.UserActor):
#     cmd = model.CreateSession(session_id=dft.SESSION_ID, user_id=dft.USER_ID)
#     await user_actor.handle(cmd)
#     assert user_actor.entity.session_ids
#     session = user_actor.select_child(dft.SESSION_ID)
#     return session


# def test_user_add_key(user_actor: service.UserActor):
#     encrypt = factory.encrypt_facotry()
#     api_type = "test"
#     api_key = encrypt.encrypt_string("random").decode()

#     idem_id = encrypt.hash_string(api_type + api_key).hex()
#     cmd = model.UserAPIKeyAdded(
#         user_id=user_actor.entity_id,
#         api_key=api_key,
#         api_type=api_type,
#         idem_id=idem_id,
#     )
#     user_actor.apply(cmd)


# def sendchatmessage(chat_message: model.ChatMessage):
#     return model.SendChatMessage(
#         session_id=dft.SESSION_ID,
#         user_id=dft.USER_ID,
#         message_body=chat_message.content,
#         role=chat_message.role,
#         client_type="askgpt_test",
#     )


# async def test_system_cache(gptsystem: service.GPTSystem):
#     system_cache = gptsystem.cache
#     assert system_cache is not None
#     assert isinstance(system_cache, Cache)


# async def test_ask_question(
#     session_actor: service.SessionActor,
#     chat_messages: list[model.ChatMessage],
#     openai_client: OpenAIClient,
# ):
#     pre_test_msg_cnt = session_actor.message_count
#     prompt = chat_messages[0]  # type: ignore

#     resp = session_actor.send_chatmessage(
#         client=openai_client,
#         message=prompt,
#         completion_model="gpt-3.5-turbo",
#         options=dict(stream=True),
#     )
#     ans = ""
#     async for c in resp:
#         ans += c

#     assert ans == "pong"

#     assert session_actor.message_count == pre_test_msg_cnt + 2


# async def test_session_self_rebuild(eventstore: EventStore):
#     async with eventstore._uow.trans():
#         events = await eventstore.get(dft.SESSION_ID)
#     created = model.SessionCreated(
#         user_id=dft.USER_ID,
#         session_id=dft.SESSION_ID,
#         session_name="New Session",
#     )

#     session_actor = service.SessionActor.apply(created)

#     session_actor.rebuild(events)

#     assert isinstance(session_actor, service.SessionActor)
#     assert session_actor.entity_id == dft.SESSION_ID
#     assert (
#         session_actor.entity.messages[0].asdict() == events[0].asdict()["chat_message"]
#     )
#     assert (
#         session_actor.entity.messages[1].asdict() == events[1].asdict()["chat_message"]
#     )


# async def test_user_rebuild_session(user_actor: service.UserActor):
#     current_ss_actor = user_actor.select_child(dft.SESSION_ID)

#     user_built_session = await user_actor.rebuild_session(session_id=dft.SESSION_ID)

#     assert current_ss_actor is not user_built_session

#     assert current_ss_actor.entity_id == user_built_session.entity_id == dft.SESSION_ID
#     assert (
#         current_ss_actor.entity.user_id
#         == user_built_session.entity.user_id
#         == dft.USER_ID
#     )

#     assert current_ss_actor.message_count == user_built_session.message_count


# async def test_user_self_rebuild(eventstore: EventStore):
#     async with eventstore._uow.trans():
#         user_events = await eventstore.get(dft.USER_ID)
#     user_created = user_events[0]
#     user_actor = service.UserActor.apply(user_created)
#     user_actor.rebuild(user_events[1:])
#     assert user_actor.entity_id == dft.USER_ID
#     assert user_actor.session_count == 1


# async def test_system_rebuild_user(
#     gptsystem: service.GPTSystem, user_actor: service.UserActor
# ):
#     built_user = await gptsystem.rebuild_user(user_actor.entity_id)
#     assert built_user is not user_actor
#     assert built_user.entity_id == user_actor.entity_id == dft.USER_ID
#     assert built_user.session_count == user_actor.session_count == 1


# async def test_user_rebuild_fail():
#     e = model.Event(entity_id="random")

#     with pytest.raises(NotImplementedError):
#         service.UserActor.apply(None)

#     with pytest.raises(NotImplementedError):
#         service.UserActor.apply(e)
