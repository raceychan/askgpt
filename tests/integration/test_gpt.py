import pytest

from src.app.actor import MailBox, QueueBox
from src.app.gpt import errors, gptsystem, model, service
from src.domain import config
from src.domain.model.test_default import TestDefaults
from src.infra.cache import MemoryCache
from src.infra.eventstore import EventStore


class EchoMailbox(MailBox):
    async def publish(self, message: str):
        print(message)


@pytest.fixture(scope="module")
async def gpt_system(settings: config.Settings, eventstore: service.EventStore):
    system = service.GPTSystem(
        boxfactory=QueueBox,
        ref=settings.actor_refs.SYSTEM,
        settings=settings,
        cache=MemoryCache(),
    )
    await system.start(eventstore=eventstore)
    return system


@pytest.fixture(scope="module")
def create_user():
    return model.CreateUser(user_id=TestDefaults.USER_ID)


@pytest.fixture(scope="module")
def create_session():
    return model.CreateSession(
        user_id=TestDefaults.USER_ID, session_id=TestDefaults.SESSION_ID
    )


@pytest.fixture(scope="module")
def send_chat_message():
    return model.SendChatMessage(
        user_id=TestDefaults.USER_ID,
        session_id=TestDefaults.SESSION_ID,
        message_body="hello",
        role="user",
    )


@pytest.fixture(scope="module")
def system_started(settings: config.Settings):
    return gptsystem.SystemStarted(entity_id=TestDefaults.SYSTEM_ID, settings=settings)


@pytest.fixture(scope="module")
def user_created():
    dfs = TestDefaults
    return model.UserCreated(user_id=dfs.USER_ID)  # , user_info=dfs.USER_INFO)


@pytest.fixture(scope="module")
def session_created():
    return model.SessionCreated(
        user_id=TestDefaults.USER_ID, session_id=TestDefaults.SESSION_ID
    )


async def test_create_user_from_system(
    gpt_system: service.GPTSystem,
    eventstore: EventStore,
    create_user: model.CreateUser,
):
    defaults = TestDefaults
    command = model.CreateUser(
        user_id=defaults.USER_ID
    )  # , user_info=defaults.USER_INFO)

    await gpt_system.receive(command)

    user = gpt_system.get_child(command.entity_id)
    assert isinstance(user, service.UserActor)

    user_events = await eventstore.get(create_user.entity_id)
    assert len(user_events) == 1
    assert isinstance(user_events[0], model.UserCreated)


async def test_system_get_user_actor(gpt_system: service.GPTSystem):
    user = gpt_system.get_child(TestDefaults.USER_ID)
    assert isinstance(user, service.UserActor)
    return user


async def test_system_get_journal(gpt_system: service.GPTSystem):
    journal = gpt_system.journal
    assert isinstance(journal, gptsystem.Journal)


async def test_user_get_journal(gpt_system: service.GPTSystem):
    user = gpt_system.get_child(TestDefaults.USER_ID)
    assert isinstance(user, service.UserActor)

    journal = user.system.journal
    assert isinstance(journal, gptsystem.Journal)


async def test_create_user_by_command(
    gpt_system: service.GPTSystem, create_user: model.CreateUser
):
    await gpt_system.handle(create_user)

    user = gpt_system.get_child(create_user.entity_id)
    assert isinstance(user, service.UserActor)


async def test_create_session_by_command(
    gpt_system: service.GPTSystem,
    create_session: model.CreateSession,
    eventstore: EventStore,
):
    user = gpt_system.select_child(create_session.user_id)

    await user.handle(create_session)

    session = user.select_child(create_session.entity_id)
    assert isinstance(session, service.SessionActor)

    user_events = await eventstore.get(user.entity_id)
    assert isinstance(user_events[-1], model.SessionCreated)


async def test_create_user_by_event(user_created: model.UserCreated):
    user = service.UserActor.apply(user_created)
    assert isinstance(user, service.UserActor)
    assert user.entity_id == user_created.entity_id


async def test_create_session_by_event(session_created: model.SessionCreated):
    session = service.SessionActor.apply(session_created)
    assert isinstance(session, service.SessionActor)
    assert session.entity_id == session_created.session_id


async def test_send_message_receive_response(
    gpt_system: service.GPTSystem, send_chat_message: model.SendChatMessage
):
    ...


async def test_event_unduplicate(
    eventstore: service.EventStore,
    system_started: gptsystem.SystemStarted,
    user_created: model.UserCreated,
    session_created: model.SessionCreated,
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

    all_events_set = set(all_events)
    assert (
        all_events_set - system_events_set - user_events_set - session_events_set
        == set()
    )


def test_service_state_start():
    state = service.SystemState.created
    new_state = state.start()
    assert new_state == service.SystemState.running

    with pytest.raises(errors.InvalidStateError):
        service.SystemState.running.start()


def test_service_state_stop():
    state = service.SystemState.running
    new_state = state.stop()
    assert new_state == service.SystemState.stopped

    with pytest.raises(errors.InvalidStateError):
        service.SystemState.stopped.stop()


@pytest.fixture(scope="module")
async def gpt_service(settings: config.Settings):
    gpt = service.GPTService.from_settings(settings)
    async with gpt.lifespan():
        yield gpt


@pytest.mark.skip(reason="TODO: fix this test")
async def test_start_when_already_running(gpt_service: service.GPTService):
    gpt_service.state = service.SystemState.running
    await gpt_service.start()
    assert gpt_service.state.is_running

    # Assert that no further actions are taken if the state is already running
    assert gpt_service.system.state.is_running

    await gpt_service.stop()
    assert gpt_service.state.is_stopped
