from askgpt.api.errors import EntityNotFoundError, GeneralWebError, ThrottlingError
from askgpt.app.auth.errors import AuthenticationError


class InvalidStateError(Exception): ...


class UserNotRegisteredError(AuthenticationError): ...


class GPTError(GeneralWebError):
    service = "gpt"


class SessionNotFoundError(EntityNotFoundError, GPTError):
    def __init__(self, session_id: str):
        msg = f"Session {session_id} not found"
        super().__init__(msg)


class OrphanSessionError(GPTError):
    "You are accessing a session that does not belong to you, if you believe this is an error, please contact support."

    def __init__(self, session_id: str, user_id: str):
        msg = f"Session {session_id} does not belong to user {user_id}"
        super().__init__(msg)


class APIKeyNotProvidedError(GPTError):
    """
    You would need to register you api-key first before sending messages
    """

    def __init__(self, api_type: str):
        msg = f"You do not have any registered api-key for {api_type}"
        super().__init__(msg)


class APIKeyNotAvailableError(GPTError, ThrottlingError):
    def __init__(self, api_type: str):
        msg = f"No API keys available for {api_type=}"
        super().__init__(msg)


class OpenAIRequestError(GPTError):
    status_code: int

    def __init__(self, status_code: int, message: str):
        msg = f"OpenAI request failed with status code {status_code}: {message}"
        self.status_code = status_code
        super().__init__(msg)
