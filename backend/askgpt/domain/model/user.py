from askgpt.domain.model.base import Command, Event, Field


class CreateUser(Command):
    entity_id: str = Field(alias="user_id")


class UserCreated(Event):
    entity_id: str = Field(alias="user_id")
