
# from app.interface import AbstractActor  # , ActorRef  # , ActorRegistry
from app.journal import Journal

# from domain import Settings

# from domain.interface import EventLogRef, JournalRef  # , SystemRef

import typing as ty
ActorRef = str

TChildRefs = ty.TypeVar("TChildRefs")  # , bound=ActorRef)
TChild = ty.TypeVar("TChild")  # , bound=AbstractActor)


class Actor(ty.Generic[TChildRefs, TChild]):
    childs: dict[TChildRefs, TChild]


# class EventLog(Actor):
#     ...


class JournalRef(ActorRef):
    ...


SystemChildRef = ty.TypeVar("SystemChildRef")  # , bound=JournalRef)
SystemChild = ty.TypeVar("SystemChild")  # , bound=Journal)


class System(Actor[SystemChildRef, SystemChild]):
    # _settings: Settings

    @property
    def journal(self):
        # ref = self._settings.actor_refs.JOURNAL

        return self.childs[JournalRef("journal")]
