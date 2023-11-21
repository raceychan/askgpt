import bcrypt

from src.domain.config import settings

salt = bcrypt.gensalt()


def hash_password(password: bytes) -> bytes:
    return bcrypt.hashpw(password, salt)


def verify_password(password: bytes, hashed: bytes) -> bool:
    return bcrypt.checkpw(password, hashed)
