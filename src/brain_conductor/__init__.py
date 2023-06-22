"""
Main module for the Brain Conductor web application. It contains the
Quart app factory.
"""
import asyncio
import json
from json import JSONDecodeError
from typing import Literal
from dataclasses import dataclass

import aioboto3
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from pydantic import ValidationError
from quart import Quart, render_template, websocket, Response, request
from werkzeug.exceptions import BadRequest

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
from .models import ContactUs, Feedback
from .personas import PERSONAS
from .services import DeliveryError, AWSSESEmailService
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
    service_name: str


def get_quart_app(
    name: str,
    openai_api_key: str,
    chat_completion_model: str,
    text_completion_model: str,
    log_level: LogLevel,
    google_measurement_id: str | Literal[False],
    coin_market_cap_api_key: str,
    hugging_face_access_token: str,
    aws_region: str,
    aws_access_key_id: str,
    aws_secret_access_key: str,
    sender_email_address: str,
    contact_us_recipients: list[str],
    promoted_persona_count: int,
    feedback_recipients: list[str],
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
    :param aws_secret_access_key: Secret key for AWS
    :param aws_access_key_id: Access key ID for AWS
    :param aws_region: Region for AWS
    :param sender_email_address: Address to place in "from" for emails
    :param contact_us_recipients: Addresses to place in "to" for contact us emails
    :param promoted_persona_count: How many personas to present to the
                                    user upon starting a session.
    :param feedback_recipients: Addresses to place in "to" for feedback emails
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

    @app.before_serving
    async def startup():
        """Startup"""
        session = aioboto3.Session(
            region_name=aws_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
        app.ses_client = session.client("ses")
        app.email_service = AWSSESEmailService(await app.ses_client.__aenter__())

    @app.after_serving
    async def shutdown():
        """Shutdown"""
        if hasattr(app, "ses_client"):
            await app.ses_client.__aexit__(None, None, None)

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

    @app.post("/contact-us")
    async def contact_us() -> Response:
        """Contact form submission endpoint"""
        try:
            form_data = await request.form
            contact_us_data = ContactUs(**form_data)
            if contact_us_data.name:
                app.logger.info("Honeypot field is filled")
            else:
                html, text = await asyncio.gather(
                    render_template(
                        "email_contact_us.html",
                        name=contact_us_data.name_honeypot,
                        email=contact_us_data.email_honeypot,
                        message=contact_us_data.comments,
                    ),
                    render_template(
                        "email_contact_us.txt",
                        name=contact_us_data.name_honeypot,
                        email=contact_us_data.email_honeypot,
                        message=contact_us_data.comments,
                    ),
                )
                await app.email_service.send_email(  # type: ignore[attr-defined]
                    sender=sender_email_address,
                    recipients=contact_us_recipients,
                    subject=f"Contact Us Received from {contact_us_data.email_honeypot}",
                    body_text=text,
                    body_html=html,
                )
            return Response(None, 204)
        except ValidationError as e:
            return Response(e.json(indent=0), 400, mimetype="text/json")
        except (BadRequest, TypeError):
            return Response(
                json.dumps(
                    [
                        {
                            "loc": [],
                            "msg": "An error occurred processing the request!",
                        }
                    ]
                ),
                400,
                mimetype="text/json",
            )
        except DeliveryError as e:
            app.logger.exception("Unable to send email for contact us", exc_info=e)
            return Response(
                json.dumps(
                    [
                        {
                            "loc": [],
                            "msg": "An error occurred completing the request!",
                        }
                    ]
                ),
                400,
                mimetype="text/json",
            )

    @app.post("/feedback")
    async def feedback() -> Response:
        """Feedback submission endpoint"""
        try:
            form_data = await request.json
            feedback_data = Feedback(**form_data)
            html = await render_template(
                "email_feedback.html",
                question=feedback_data.question,
                answer=feedback_data.answer,
                message=feedback_data.message,
                chat_history=feedback_data.chat_history,
            )
            await app.email_service.send_email(  # type: ignore[attr-defined]
                sender=sender_email_address,
                recipients=feedback_recipients,
                subject="Feedback",
                body_html=html,
                body_text="",
            )
            return Response(None, 204)
        except ValidationError as e:
            return Response(e.json(indent=0), 400, mimetype="text/json")
        except (BadRequest, TypeError):
            return Response(
                json.dumps(
                    [
                        {
                            "loc": [],
                            "msg": "An error occurred processing the request!",
                        }
                    ]
                ),
                400,
                mimetype="text/json",
            )
        except DeliveryError as e:
            app.logger.exception("Unable to send email for feedback", exc_info=e)
            return Response(
                json.dumps(
                    [
                        {
                            "loc": [],
                            "msg": "An error occurred completing the request!",
                        }
                    ]
                ),
                400,
                mimetype="text/json",
            )

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
