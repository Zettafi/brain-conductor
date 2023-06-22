"""
QUart application WSGI module
"""
import os

from brain_conductor import get_quart_app, TracingConfig, LogLevel
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
        if not default and required:
            raise RuntimeError(f"{name} env variable is required!")
    return default


openai_api_key = get_env_var("OPENAI_API_KEY")
log_level: str | LogLevel = get_env_var("LOG_LEVEL", False, "ERROR").upper()
google_measurement_id: str | Literal[False] = os.getenv("GOOGLE_MEASUREMENT_ID", False)
coin_market_cap_api_key = get_env_var("COIN_MARKET_CAP_API_KEY")
hugging_face_access_token = get_env_var("HUGGING_FACE_ACCESS_TOKEN")
promoted_persona_count = int(get_env_var("PROMOTED_PERSONA_COUNT", default="3"))

tracing_config = TracingConfig(
    enabled=True
    if get_env_var("TRACING_ENABLED", default="false").lower() == "true"
    else False,
    debug=True
    if get_env_var("TRACING_DEBUG", default="false").lower() == "true"
    else False,
    service_name=get_env_var("TRACING_SERVICE_NAME", default="brain-conductor"),
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
    promoted_persona_count=promoted_persona_count,
    tracing_config=tracing_config,
)
