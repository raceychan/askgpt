from askgpt.app.api.errors import ClientSideError, EntityNotFoundError, ThrottlingError
from askgpt.app.auth.errors import AuthenticationError

class InvalidStateError(Exception):
    ...

class GPTError(ClientSideError):
    service = "gpt"


class UserNotRegisteredError(AuthenticationError): ...


class SessionNotFoundError(EntityNotFoundError, GPTError):
    def __init__(self, session_id: str):
        msg = f"Session {session_id} not found"
        super().__init__(msg)


class OrphanSessionError(AuthenticationError):
    "You are accessing a session that does not belong to you, if you believe this is an error, please contact support."

    def __init__(self, session_id: str, user_id: str):
        msg = f"Session {session_id} does not belong to user {user_id}"
        super().__init__(msg)


class APIKeyNotProvidedError(AuthenticationError):
    def __init__(self, user_id: str, api_type: str):
        msg = f"User {user_id} do not have any API-key for {api_type}"
        super().__init__(msg)


class APIKeyNotAvailableError(ThrottlingError):
    def __init__(self, api_type: str):
        msg = f"No API keys available for {api_type=}"
        super().__init__(msg)
