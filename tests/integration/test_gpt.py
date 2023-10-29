import pytest

from src.app.actor import MailBox
from src.app.gpt import service
from src.app.journal import EventStore
from src.domain.config import TestDefaults


class EchoMailbox(MailBox):
    async def publish(self, message):
        print(message)


@pytest.fixture(scope="module")
async def gpt_system(settings, eventstore):
    system = await service.GPTSystem.create(settings, eventstore=eventstore)
    return system


@pytest.fixture(scope="module")
def create_user():
    return service.CreateUser(user_id=TestDefaults.user_id)


@pytest.fixture(scope="module")
def create_session():
    return service.CreateSession(
        user_id=TestDefaults.user_id, session_id=TestDefaults.session_id
    )


@pytest.fixture(scope="module")
def send_chat_message():
    return service.SendChatMessage(
        user_id=TestDefaults.user_id,
        session_id=TestDefaults.session_id,
        user_message="hello",
    )


@pytest.fixture(scope="module")
def system_started(settings):
    return service.SystemStarted(entity_id=TestDefaults.system_id, settings=settings)


@pytest.fixture(scope="module")
def user_created():
    return service.UserCreated(user_id=TestDefaults.user_id)


@pytest.fixture(scope="module")
def session_created():
    return service.SessionCreated(
        user_id=TestDefaults.user_id, session_id=TestDefaults.session_id
    )


async def test_create_user_from_system(
    gpt_system: service.GPTSystem,
    eventstore: EventStore,
    create_user: service.CreateUser,
):
    command = service.CreateUser(user_id=TestDefaults.user_id)
    await gpt_system.receive(command)
    user = gpt_system.get_actor(command.entity_id)
    assert isinstance(user, service.UserActor)

    user_events = await eventstore.get(create_user.entity_id)
    assert len(user_events) == 1
    assert isinstance(user_events[0], service.UserCreated)


async def test_system_get_user_actor(gpt_system):
    user = gpt_system.get_actor(TestDefaults.user_id)
    assert isinstance(user, service.UserActor)
    return user


async def test_system_get_journal(gpt_system):
    journal = gpt_system.get_actor("journal")
    assert isinstance(journal, service.Journal)


async def test_user_get_journal(gpt_system):
    user = gpt_system.get_actor(TestDefaults.user_id)
    assert isinstance(user, service.UserActor)

    journal = user.system.get_actor("journal")
    assert isinstance(journal, service.Journal)


async def test_create_user_by_command(
    gpt_system: service.GPTSystem, create_user: service.CreateUser
):
    await gpt_system.handle(create_user)

    user = gpt_system.get_actor(create_user.entity_id)
    assert isinstance(user, service.UserActor)


async def test_create_session_by_command(
    gpt_system: service.GPTSystem,
    create_session: service.CreateSession,
    eventstore: EventStore,
):
    user = gpt_system.get_actor(create_session.user_id)
    assert isinstance(user, service.UserActor)

    await user.handle(create_session)
    session = user.get_actor(create_session.entity_id)
    assert isinstance(session, service.SessionActor)

    session_events = await eventstore.get(create_session.entity_id)
    assert len(session_events) == 1
    assert isinstance(session_events[0], service.SessionCreated)


async def test_create_user_by_event(user_created: service.UserCreated):
    user = service.UserActor.apply(user_created)
    assert isinstance(user, service.UserActor)
    assert user.entity_id == user_created.entity_id


async def test_create_session_by_event(session_created: service.SessionCreated):
    session = service.SessionActor.apply(session_created)
    assert isinstance(session, service.SessionActor)
    assert session.entity_id == session_created.entity_id


async def test_event_unduplicate(
    eventstore,
    system_started: service.SystemStarted,
    user_created: service.UserCreated,
    session_created: service.SessionCreated,
):
    system_events = await eventstore.get(system_started.entity_id)
    system_events_set = set(system_events)
    assert len(system_events) == len(system_events_set)

    user_events = await eventstore.get(user_created.entity_id)
    user_events_set = set(user_events)
    assert len(user_events) == len(user_events_set)

    session_events = await eventstore.get(session_created.entity_id)
    session_events_set = set(session_events)
    assert len(session_events) == len(session_events_set)

    all_events = await eventstore.list_all()
    assert isinstance(all_events[0], service.SystemStarted)
    assert isinstance(all_events[-1], service.SystemStoped)

    all_events_set = set(all_events)
    assert (
        all_events_set - system_events_set - user_events_set - session_events_set
        == set()
    )
