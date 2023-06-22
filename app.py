"""
QUart application WSGI module
"""
import os

from brain_conductor import get_quart_app, TracingConfig
from typing import Literal

try:
    # noinspection PyUnresolvedReferences
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


def get_env_var(name: str, required: bool = True, default: str | None = None):
    """
    Get an environment variable. If variable is not in the environment, the function
    will error if required or return default if not.
    :param name: Name of the environment variable.
    :param required: Is the environment required to contain the variable?
    :param default: Default value to return when the environment does not contain the
     variable.
    :return: Value for the variable in the environment if found or the default value
    """
    try:
        return os.environ[name]
    except KeyError:
        if required:
            raise RuntimeError(f"{name} env variable is required!")
    return default


openai_api_key = get_env_var("OPENAI_API_KEY")
log_level = get_env_var("LOG_LEVEL", False, "ERROR").upper()
google_measurement_id: str | Literal[False] = os.getenv("GOOGLE_MEASUREMENT_ID", False)
coin_market_cap_api_key = get_env_var("COIN_MARKET_CAP_API_KEY")
hugging_face_access_token = get_env_var("HUGGING_FACE_ACCESS_TOKEN")
aws_region = get_env_var("AWS_REGION")
aws_access_key_id = get_env_var("AWS_ACCESS_KEY_ID")
aws_secret_access_key = get_env_var("AWS_SECRET_ACCESS_KEY")
sender_email_address = get_env_var("SENDER_EMAIL_ADDRESS")
contact_us_recipients = [
    recipient.strip() for recipient in get_env_var("CONTACT_US_RECIPIENTS").split(",")
]
promoted_persona_count = int(
    get_env_var("PROMOTED_PERSONA_COUNT", required=False, default="3")
)
feedback_recipients = [
    recipient.strip() for recipient in get_env_var("FEEDBACK_RECIPIENTS").split(",")
]

tracing_config = TracingConfig(
    enabled=True
    if get_env_var("TRACING_ENABLED", required=False, default="false").lower() == "true"
    else False,
    debug=True
    if get_env_var("TRACING_DEBUG", required=False, default="false").lower() == "true"
    else False,
    service_name=get_env_var("TRACING_SERVICE_NAME", required=False),
)

app = get_quart_app(
    name="Brain Conductor",
    openai_api_key=openai_api_key,
    chat_completion_model="gpt-3.5-turbo",
    text_completion_model="text-davinci-003",
    log_level=log_level,
    google_measurement_id=google_measurement_id,
    coin_market_cap_api_key=coin_market_cap_api_key,
    hugging_face_access_token=hugging_face_access_token,
    aws_region=aws_region,
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    sender_email_address=sender_email_address,
    contact_us_recipients=contact_us_recipients,
    promoted_persona_count=promoted_persona_count,
    feedback_recipients=contact_us_recipients,
    tracing_config=tracing_config,
)
