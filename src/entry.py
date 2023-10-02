import openai


from domain.config import Config
from domain.model import Entity, Command, Event, ValueObject, Field, uuid_factory

from app.actor import Actor

from infra.mq import MailBox, QueueBroker
from infra.eventstore import EventStore


def aggregate_root(cls: type[Entity]) -> type[Entity]:
    return cls


class ChatMessage(ValueObject):
    content: str
    is_user_message: bool


class ChatSession(Entity):
    session_id: str = Field(alias="entity_id", default_factory=uuid_factory)
    user_id: str
    messages: list[ChatMessage] = Field(default_factory=list)


@aggregate_root
class User(Entity):
    """
    Aggregate Root
    """

    user_id: str = Field(alias="entity_id")
    chat_sessions: dict[str, ChatSession] = Field(default_factory=dict)

    def add_new_session(self):
        new_session = ChatSession(user_id=self.user_id)
        self.chat_sessions[new_session.session_id] = new_session
