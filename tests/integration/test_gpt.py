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


async def test_create_user_from_mediator(mediator: Mediator):
    command = service.CreateUser(user_id=TestDefaults.user_id)
    await mediator.receive(command)

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

