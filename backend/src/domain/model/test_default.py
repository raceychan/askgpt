from src.app.auth.model import UserRoles
from src.domain.model.user import UserInfo
from src.infra import encrypt


class TestDefaults:
    SYSTEM_ID: str = "system"
    USER_ID: str = "5aba4f79-19f7-4bd2-92fe-f2cdb43635a3"
    USER_NAME: str = "admin"
    USER_EMAIL: str = "admin@gmail.com"
    USER_PASSWORD: str = "password"
    SESSION_ID: str = "e0b5ee4a-ef76-4ed9-89fb-5f7a64122dc8"
    SESSION_NAME: str = "default_session"
    MODEL: str = "gpt-3.5-turbo"
    USER_ROLE: UserRoles = UserRoles.user
    USER_INFO: UserInfo = UserInfo(
        user_email=USER_EMAIL,
        user_name=USER_NAME,
        hash_password=encrypt.hash_password(USER_PASSWORD.encode()),
    )
