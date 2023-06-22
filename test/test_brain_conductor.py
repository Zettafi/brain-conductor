import unittest
from inspect import iscoroutine

from brain_conductor import get_quart_app, TracingConfig


class AppFactoryTestCase(unittest.TestCase):
    def test_factory_returns_quart_app(self):
        app = get_quart_app(
            name="Test App",
            openai_api_key="API Key",
            chat_completion_model="Chat Model",
            text_completion_model="Text Model",
            log_level="ERROR",
            google_measurement_id="G-DUB",
            coin_market_cap_api_key="CMC Key",
            hugging_face_access_token="Hugging Face Key",
            aws_region="REGION",
            aws_access_key_id="Key ID",
            aws_secret_access_key="So secret",
            sender_email_address="no-reply@chainconductor.io",
            contact_us_recipients=["info@chainconductor.io"],
            promoted_persona_count=3,
            feedback_recipients=["feedback@chainconductor.io"],
            tracing_config=TracingConfig(True, True, "testing"),
        )
        # noinspection PyTypeChecker
        coroutine = app(scope=None, receive=None, send=None)
        self.assertTrue(
            iscoroutine(coroutine),
            "get_quart_app did not return a coroutine function",
        )
        coroutine.close()
