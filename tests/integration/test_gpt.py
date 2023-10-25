import pytest
from src.app.actor import MailBox, Mediator
from src.app.gpt import service
from src.domain.config import TestDefaults


class EchoMailbox(MailBox):
    async def publish(self, message):
        print(message)


@pytest.fixture(scope="module")
async def gpt_system(settings):
    return await service.GPTSystem.create(settings)


@pytest.fixture(scope="module")
def mediator(gpt_system):
    mdr =  Mediator(mailbox=MailBox.build())
    return mdr

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
def user_created():
    return service.UserCreated(user_id=TestDefaults.user_id)


@pytest.fixture(scope="module")
def session_created():
    return service.SessionCreated(
        user_id=TestDefaults.user_id, session_id=TestDefaults.session_id
    )



async def test_create_user_from_mediator(mediator: Mediator):
    command = service.CreateUser(user_id=TestDefaults.user_id)
    await mediator.receive(command)

    # NOTE: if we use asyncio.create_task in on_receive
    # we wouldn't be able to get actor from mediator

    user = mediator.system.get_actor(command.entity_id)
    assert isinstance(user, service.UserActor)


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

# @pytest.fixture(scope="module")
# async def system(settings):
#     system = await GPTSystem.create(settings)
#     return system


async def test_create_user_by_command(gpt_system: service.GPTSystem, create_user: service.CreateUser):
    await gpt_system.handle(create_user)

    user = gpt_system.get_actor(create_user.entity_id)
    assert isinstance(user, service.UserActor)


async def test_create_session_by_command(
    gpt_system: service.GPTSystem, create_session: service.CreateSession
):
    user = gpt_system.get_actor(create_session.user_id)
    assert isinstance(user, service.UserActor)

    await user.handle(create_session)
    session = user.get_actor(create_session.entity_id)
    assert isinstance(session, service.SessionActor)


async def test_create_user_by_event(user_created: service.UserCreated):
    user = service.UserActor.apply(user_created)
    assert isinstance(user, service.UserActor)
    assert user.entity_id == user_created.entity_id


async def test_create_session_by_event(session_created: service.SessionCreated):
    session = service.SessionActor.apply(session_created)
    assert isinstance(session, service.SessionActor)
    assert session.entity_id == session_created.entity_id
