import typing as ty

import pytest

from src.app.actor import MailBox, System
from src.app.auth.model import UserAuth
from src.app.journal import Journal
from src.app.model import UserCreated
from src.domain.config import Settings
from src.infra.eventstore import EventStore


class EchoMailbox(MailBox):
    async def publish(self, message: str):
        print(message)


@pytest.fixture(scope="module", autouse=True)
async def base_system(settings: Settings):
    base_systm = System[ty.Any](
        mailbox=MailBox.build(),
        ref=settings.actor_refs.SYSTEM,
        settings=settings,
    )

    return base_systm


@pytest.fixture(scope="module")
def journal(eventstore: EventStore, settings: Settings):
    return Journal(
        eventstore=eventstore,
        mailbox=EchoMailbox.build(),
        ref=settings.actor_refs.JOURNAL,
    )


async def test_system_publishes_event_to_journal(
    base_system: System[ty.Any],
    user_auth: UserAuth,
    journal: Journal,  # journal is needed to test publish method
    eventstore: EventStore,
):
    event = UserCreated(user_id=user_auth.entity_id, user_info=user_auth.user_info)
    await base_system.publish(event)
    user_events = await eventstore.get(entity_id=user_auth.entity_id)
    assert user_events[0] == event
