from src.app.api.errors import ClientSideError, EntityNotFoundError


class AuthenticationError(ClientSideError):
    service: str = "auth"


class UserNotFoundError(EntityNotFoundError, AuthenticationError):
    """
    Unable to find user with the same email
    """

    service: str = "auth"

    def __init__(self, *, user_email: str):
        msg = f"user {user_email} not found"
        super().__init__(msg)


class InvalidPasswordError(AuthenticationError):
    """
    User email and password does not match
    """


class UserAlreadyExistError(AuthenticationError):
    """
    User with the same email already exist
    """


class InvalidCredentialError(AuthenticationError):
    """
    Could not validate user credentials
    """


class UserAPIKeyNotProvidedError(AuthenticationError):
    """
    User API key not provided
    """

    def __init__(self, *, user_id: str, api_type: str):
        msg = f"user {user_id} api key not provided for {api_type}"
        super().__init__(msg)
