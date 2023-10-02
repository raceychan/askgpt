import openai

from functools import singledispatchmethod

from app.actor import Actor
from domain.model import Ask, AskHistory, Event, AskQuestion, AskAnswered, Message
from infra.mq import MailBox


class ApplicationService:
    ...


class GPTService(ApplicationService):
    ...
    repository: ...


class Student(Actor):
    def __init__(self, history: AskHistory):
        self.history = history

    # def send(self, message: "Message", professor: Actor):
    #     professor.receive(cmd)

    def ask(self, question: str, professor: Actor):
        ask = Ask(question=question)
        cmd = AskQuestion(ask=ask)

        self.history.add_ask(ask)
        self.send(cmd, professor)

    def _handle(self, message: Message):
        ...


class Professor(Actor):
    endpoit_uri = "kafka.gpt.question_answered"

    def __init__(
        self, history: AskHistory, mailbox: MailBox, kb: openai.ChatCompletion
    ):
        self.history = history
        self.mailbox = mailbox
        self.kb = kb

    def answer(self, ask: Ask) -> str:
        from rich.console import Console

        console = Console()

        context = self.history.as_context()
        model = "gpt-3.5-turbo"
        try:
            chat_resp = self.kb.create(model=model, stream=True, messages=context)
        except Exception as e:
            raise e
        else:
            console.print("question sent to openai")

        console.rule("[bold red]Answer")
        console.print("")

        answer = ""
        for resp in chat_resp:
            for choice in resp.choices:  # type: ignore
                content = choice.get("delta", {}).get("content")
                if content:
                    answer += content
                    console.print(content, end="")
        self.history.answer_ask(ask.ask_id, answer)
        print(f"{ask} is answerd: {answer}")
        return answer

    @singledispatchmethod
    def _handle(self, message: Message):
        ...

    @_handle.register
    def _(self, command: AskQuestion):
        self.answer(command.ask)
        self.publish(
            AskAnswered(history_id=self.history.history_id, ask=command.ask)  # type: ignore
        )

    def publish(self, event: Event):
        self.mailbox.put(event)
