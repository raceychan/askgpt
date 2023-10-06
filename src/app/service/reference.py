from domain.model import Entity, Event,Command, uuid_factory, timestamp_factory, utc_datetime
from pydantic import Field


class ChatSessionStartedEvent(Event):
    session_id: str
    user_id: str = Field(alias="entity_id")


class MessageSentEvent(Event):
    session_id: str
    message: ChatMessage


class Message(Command):
    content: str
    message_type: str

import queue
# Define ChatSessionActor
class ActorSystem:
    def __init__(self):
        self.actors = {}
        self.message_queue = queue.Queue()
        self.shutdown_flag = threading.Event()

    def actor_of(self, actor_class, name=None):
        actor_id = name or str(uuid.uuid4())
        actor_ref = ActorRef(self, actor_id, actor_class)

        self.actors[actor_id] = actor_ref
        actor_ref.start()
        return actor_ref

    def stop_actor(self, actor_id):
        actor_ref = self.actors.get(actor_id)
        if actor_ref:
            actor_ref.stop()
            del self.actors[actor_id]

    def shutdown(self):
        self.shutdown_flag.set()
        for actor_id in list(self.actors.keys()):
            self.stop_actor(actor_id)

    def send_message(self, message):
        self.message_queue.put(message)


class ChatSessionActor(Actor):
    def __init__(self, user_id):
        self.session = ChatSession.create(user_id)

    def on_receive(self, message):
        if message.message_type == "UserMessage":
            self.session.send_message(message.content)
        elif message.message_type == "GetChatHistory":
            self.send_message(Message(self.session.get_chat_history(), "ChatHistory"))


# ChatSystem


class ChatSystem(Actor):
    actor_system: ActorSystem
    actors: dict = Field(default_factory=dict)

    def create_chat_session_actor(self, user_id):
        actor_ref = self.actor_system.actor_of(
            ChatSessionActor, f"chat_session_{user_id}"
        )
        self.actors[user_id] = actor_ref

    def send_user_message(self, user_id, content):
        actor_ref = self.actors.get(user_id)
        if actor_ref:
            msg = Message(content=content, "UserMessage")
            actor_ref.tell(msg)

    def get_chat_history(self, user_id):
        actor_ref = self.actors.get(user_id)
        if actor_ref:
            msg = Message(None, "GetChatHistory")
            actor_ref.tell(msg)


# Main Entry Point

if __name__ == "__main__":
    actor_system = ActorSystem()
    chat_system = ChatSystem(actor_system)

    chat_system.create_chat_session_actor("user123")
    chat_system.send_user_message("user123", "Hello, chatbot!")
    chat_system.get_chat_history("user123")


# ====================================================================================================================================================

import typing as ty
# import pykka

class Chatbot(Entity):
    users: list[str] = Field(default_factory=list)

class ChatSession(Entity):
    user_id: str
    session_id: str = Field(default_factory=uuid_factory)
    messages: list = Field(default_factory=list)
    created_at: utc_datetime = Field(default=timestamp_factory)

    def send_message(self, content):
        message = ChatMessage(content, is_user_message=True)
        self.messages.append(message)

        # Invoke GPT-3.5 API here to get the response
        response = invoke_gpt_3_api(content)
        bot_message = ChatMessage(response, is_user_message=False)
        self.messages.append(bot_message)

    def get_chat_history(self):
        return [message.content for message in self.messages]


class ChatMessage:
    content: str
    is_user_message: bool
    timestamp: utc_datetime = Field(default_factory=timestamp_factory)

class User(Entity):
    chatbot_id: str
    active: bool = False

class UserChatStarted(Event):
    user_id: str

class UserChatEnded(Event):
    user_id: str

class UserMessageSent(Event):
    user_id: str
    message: str

class StartChat(Command):
    user_id: str

class EndChat(Command):
    user_id: str

class SendMessage(Command):
    user_id: str
    message: str


class Actor:
    actor_id: str

    def start(self, *args):
        ...

    def tell(self):
        ...


class ChatbotActor(Actor):
    def __init__(self, chatbot_id: str):
        self.chatbot = Chatbot(entity_id=chatbot_id)
        self.actor_id = chatbot_id

class UserActor(Actor):
    def __init__(self, user_id, chatbot_actor: ChatbotActor):
        self.user = User(entity_id=user_id, chatbot_id=chatbot_actor.actor_id)
        self.chatbot_actor = chatbot_actor.proxy()

    def on_receive(self, message):
        command = message.get('command')
        if isinstance(command, StartChat):
            self.user.active = True
            self.chatbot_actor.add_user(self.user.entity_id)
            return UserChatStarted(entity_id=self.user.entity_id, user_id=self.user.entity_id)
        elif isinstance(command, EndChat):
            self.user.active = False
            return UserChatEnded(entity_id=self.user.entity_id, user_id=self.user.entity_id)
        elif isinstance(command, SendMessage):
            return UserMessageSent( entity_id=self.user.entity_id, message=command.message, user_id=self.user.entity_id)

chatbot_actor = ChatbotActor.start('chatbot_1').proxy()

def start_conversation(user_id, chatbot_actor):
    user_actor = UserActor.start(user_id, chatbot_actor)
    user_actor.tell({'command': StartChat(user_id=user_id)})

def main():
    start_conversation('user_1', chatbot_actor)

