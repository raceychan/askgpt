# from functools import cached_property

# from pydantic import Field, computed_field

# from src.domain.model import Command, DomainBase, Entity, Event, rich_repr, uuid_factory


# class Ask(DomainBase):
#     question: str
#     ask_id: str = Field(default_factory=uuid_factory)
#     answer: str = Field(default="")

#     @property
#     def is_answered(self):
#         return self.answer != ""

#     def set_answer(self, answer: str):
#         self.answer = answer

#     def __repr__(self):
#         return f"{self.__class__.__name__}(ask_id={self.ask_id}, question={self.question}, answer={self.answer})"


# class AskQuestion(Command):
#     ask: Ask


# class AskAnswered(Event):
#     history_id: str = Field(alias="entity_id")
#     ask: Ask

#     @computed_field
#     @cached_property
#     def event_id(self) -> str:
#         return self.ask.ask_id


# class AskHistory(Entity):
#     history_id: str = Field(default_factory=uuid_factory)
#     history: dict[str, Ask] = Field(default_factory=dict)

#     def query_ask(self, ask_id: str):
#         return self.history[ask_id]

#     def add_ask(self, ask: Ask):
#         self.history[ask.ask_id] = ask

#     def answer_ask(self, ask_id: str, answer: str):
#         self.history[ask_id].set_answer(answer)

#     def as_context(self):
#         for ask in self.history.values():
#             yield dict(role="assistant", content=ask.question)
#             if ask.is_answered:
#                 yield dict(role="professor", content=ask.answer)

#     def __repr__(self):
#         lines = rich_repr(self.__dict__)
#         return f"{self.__class__.__name__}(\t\n{lines})"
