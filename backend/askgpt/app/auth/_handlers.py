from askgpt.app.auth._model import UserSignedUp
from askgpt.infra.event_dispatch import EventBus


@EventBus.register
async def send_email_to_verify_user(
    user_signedup: UserSignedUp,
) -> None:
    """
    Send email to user to verify their email
    generate a token, send the token to user's email
    then let user carry the token to our endpoint to verify their email
    """
