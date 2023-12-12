from src.app.api.errors import ClientSideError
from src.app.auth.errors import AuthenticationError


class GPTRuntimeError(ClientSideError):
    service = "gpt"


class UserNotRegisteredError(Exception):
    ...


class InvalidStateError(Exception):
    ...


class OrphanSessionError(AuthenticationError):
    "You are accessing a session that does not belong to you, if you believe this is an error, please contact support."

    def __init__(self, session_id: str, user_id: str):
        msg = f"Session {session_id} does not belong to user {user_id}"
        super().__init__(msg)
