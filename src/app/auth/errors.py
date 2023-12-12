from src.app.api.errors import ClientSideError


class AuthenticationError(ClientSideError):
    service: str = "auth"


class UserNotFoundError(AuthenticationError):
    """
    Unable to find user with the same email
    """


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
    Could not validate credentials
    """
