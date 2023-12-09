from src.app.auth.model import AccessToken
from src.domain.config import get_setting
from src.infra import factory


def parse_access_token(token: str) -> AccessToken:
    token_encrypt = factory.get_token_encrypt(get_setting())
    decoded = token_encrypt.decrypt(token)
    access_token = AccessToken.model_validate(decoded)
    return access_token

    # authenticator.is_authenticated(token)
    # payload = jwt.decode(
    #     token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
    # )
    # token_data = TokenPayload(**payload)

    # user = session.get(User, token_data.sub)
    # if not user:
    #     raise HTTPException(status_code=404, detail="User not found")
    # return user
