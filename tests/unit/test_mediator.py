# import pytest

# from src.app.actor import Actor, Command, Mediator
# from src.infra.mq import MailBox


# @pytest.fixture
# def mediator():
#     return Mediator(mailbox=MailBox.build())


# class DumpCommand(Command):
#     message: str = "hello"


# class DumpActor(Actor):
#     def __init__(self):
#         self.msgs = list()

#     async def handle(self, command: DumpCommand):
#         self.msgs.append(command.message)


# async def test_mailbox(mediator):
#     aid = "test"
#     cmd = DumpCommand(entity_id=aid)
#     await mediator.send(cmd)
