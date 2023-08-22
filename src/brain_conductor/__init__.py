"""
Main module for the Brain Conductor web application. It contains the
Quart app factory.
"""
import asyncio
import json
from json import JSONDecodeError
from typing import Literal
from dataclasses import dataclass

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from quart import Quart, render_template, websocket, Response

from .agents import CryptoAgent, ArtAgent
from .agents.llm.openai import OpenAI
from .agents.toolkits import (
    CoinMarketCap,
    CryptoToolkit,
    TimeToolKit,
    Dates,
    ArtToolKit,
    StableDiffusion,
)
from .chat import (
    inquire,
    send_experts_message,
    add_messages_to_history,
    send_error_message,
)
from .inquiries import InquiryManager
from .personas import PERSONAS
from .utils import TaskManager

LogLevel = Literal[
    "CRITICAL",
    "DEBUG",
    "FATAL",
    "ERROR",
    "INFO",
    "WARNING",
    "FATAL",
    "FATAL",
]


@dataclass
class TracingConfig:
    enabled: bool
    debug: bool
    service_name: str | None


def get_quart_app(
    name: str,
    openai_api_key: str,
    chat_completion_model: str,
    text_completion_model: str,
    log_level: LogLevel,
    google_measurement_id: str | Literal[False],
    coin_market_cap_api_key: str,
    hugging_face_access_token: str,
    promoted_persona_count: int,
    tracing_config: TracingConfig,
) -> Quart:
    """
    Quart app factory method
    :param name: Name of the app
    :param openai_api_key: API key for the OpenAI API
    :param chat_completion_model: OpenAI model to use for chat completion
    :param text_completion_model: OpenAI model to iuse for text completion
    :param log_level: Pythin logging level
    :param google_measurement_id: ID which is used by Google to track the
    site/environment in Google Analytics.
    :param coin_market_cap_api_key: API key for the Coin Market Cap API.
    :param hugging_face_access_token: Access token for the Hugging Face API.
    :param promoted_persona_count: How many personas to present to the
                                    user upon starting a session.
    :param tracing_config: Configuration for OpenTelemetry tracing.
    :return: Quart app
    """
    resource = Resource(attributes={SERVICE_NAME: tracing_config.service_name})
    trace.set_tracer_provider(TracerProvider(resource=resource))
    if tracing_config.enabled:
        trace.get_tracer_provider().add_span_processor(  # type:ignore
            BatchSpanProcessor(OTLPSpanExporter())
        )
    if tracing_config.debug:
        trace.get_tracer_provider().add_span_processor(  # type:ignore
            BatchSpanProcessor(ConsoleSpanExporter())
        )  # type:ignore
    tracer = trace.get_tracer(__name__)

    app = Quart(name)
    app.logger.setLevel(log_level)
    agents_ = [
        CryptoAgent(
            CryptoToolkit(CoinMarketCap(coin_market_cap_api_key)), TimeToolKit(Dates())
        ),
        ArtAgent(ArtToolKit(StableDiffusion(hugging_face_access_token, OpenAI()))),
    ]

    im = InquiryManager(
        openai_api_key=openai_api_key,
        chat_model=chat_completion_model,
        text_model=text_completion_model,
        personas=PERSONAS,
        agents=agents_,
    )

    @app.get("/")
    async def index() -> str:
        """
        View function for handling home page requests.
        :return: Rendered home page template as text
        """
        return await render_template(
            "index.html", google_measurement_id=google_measurement_id
        )

    @app.get("/ping")
    async def ping() -> Response:
        """Liveness/readiness check endpoint"""
        return Response("PONG", 200, mimetype="text/text")

    @app.websocket("/chat")
    async def ws() -> None:
        """
        Quart chat websocket handler
        """
        with im as icm, TaskManager() as atm:
            atm.create_task(
                "send-experts-message", send_experts_message(promoted_persona_count)
            )
            with tracer.start_as_current_span("websocket.session"):
                while True:
                    try:
                        try:
                            received = await websocket.receive()
                            message = json.loads(received)
                            message_type = message["type"]
                            uid = message.get("id")
                            if message_type == "reconnect":
                                history = [
                                    (item["from"], item["text"])
                                    for item in message["history"]
                                ]
                                await add_messages_to_history(icm, history)
                            elif message_type == "inquiry":
                                with tracer.start_as_current_span(
                                    "websocket.request"
                                ) as request_span:
                                    inquiry = message["text"]
                                    await inquire(uid, inquiry, icm, atm, request_span)
                            else:
                                raise ValueError(
                                    f'Unknown message type "{message_type}"'
                                )
                        except (JSONDecodeError, KeyError, ValueError) as e:
                            app.logger.error(
                                f"Error parsing websocket message: {received} -- {e}"
                            )
                            await send_error_message(
                                uid, "I could not understand your message"
                            )
                    except (asyncio.CancelledError, GeneratorExit):
                        # Handle disconnect
                        break

    return app
