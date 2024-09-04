from src.app.api.errors import ClientSideError, EntityNotFoundError


class AuthenticationError(ClientSideError):
    """
    Failed to authenticate user
    """
    service: str = "auth"



class UserNotRegisteredError(AuthenticationError):
    """
    Unable to find user with the email 
    """
    def __init__(self, *, user_email: str):
        msg = f"user with email:{user_email} is not found"
        super().__init__(msg)
class UserNotFoundError(EntityNotFoundError, AuthenticationError):
    """
    Unable to find user with the same user id
    """

    def __init__(self, *, user_id: str):
        msg = f"user {user_id} is not found"
        super().__init__(msg)


class UserInactiveError(EntityNotFoundError, AuthenticationError):
    """
    User is not active
    """
    def __init__(self, *, user_id: str):
        msg = f"user {user_id} is not active"
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
