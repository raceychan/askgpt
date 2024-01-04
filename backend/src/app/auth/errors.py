from src.app.api.errors import ClientSideError


class AuthenticationError(ClientSideError):
    service: str = "auth"


class UserNotFoundError(AuthenticationError):
    """
    Unable to find user with the same email
    """

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
