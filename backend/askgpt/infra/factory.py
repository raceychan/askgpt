from askgpt.domain.config import SETTINGS_CONTEXT
from askgpt.infra.security import Encryptor


def encrypt_facotry():
    settings = SETTINGS_CONTEXT.get()
    encrypt = Encryptor(
        secret_key=settings.security.SECRET_KEY.get_secret_value(),
        algorithm=settings.security.ALGORITHM,
    )
    return encrypt
