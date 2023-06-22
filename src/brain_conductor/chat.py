"""Chat module"""
import asyncio
import json
import random
from asyncio import Task

from opentelemetry.trace.span import Span
from quart import websocket, current_app, url_for

from .errors import QuotaExceededError
from .inquiries import InquiryContextManager, InquiryResponse
from .personas import Persona, PERSONAS
from .utils import TaskManager


async def inquire(
    uid: str, inquiry: str, icm: InquiryContextManager, atm: TaskManager, span: Span
):
    """
    Make an inquiry with on or more bot personas.
    :param uid: Unique identifier of the inquiry message
    :param inquiry: Question to ask
    :param icm: Context manager for the inquiry process
    :param atm: App task manager
    :param span: Tracing span for recording conversation data for review and debugging
    """
    span.set_attribute("request.inquiry", str(inquiry))
    primary, secondaries = await icm.identify_personas(inquiry, span)
    if primary:
        await inquire_and_comment(
            icm,
            atm,
            uid,
            inquiry,
            primary,
            secondaries,
            span,
        )
    else:
        response = (
            "No one seems to want to answer your question. " "Please try again later."
        )
        span.set_attribute("response.system", response)
        await send_system_message(uid, response)


async def inquire_and_comment(
    icm: InquiryContextManager,
    atm: TaskManager,
    uid: str,
    inquiry: str,
    primary: Persona,
    secondaries: list[Persona],
    span: Span,
):
    """
    Send an inquiry to a primary chatbot persona and have the secondary personas comment
    :param uid: Unique identifier of the request message
    :param icm: Inquiry context manager for the session
    :param atm: App task manager
    :param inquiry: Message to inquire
    :param primary: Primary chatbot persona to send the inquiry
    :param secondaries: Secondary chatbot personas to comment
    :param span: Tracing span for tracing and debugging
    """
    tasks: list[Task] = []
    try:
        tasks.append(
            atm.create_task(
                "send-preparing-response-message",
                send_preparing_response_message(primary.name, primary.initial_greeting),
            )
        )
        response: InquiryResponse = await icm.inquire(primary, inquiry)
        span.set_attribute(f"response.{primary.prompt_name}", response.message)
        tasks.append(
            atm.create_task(
                "send-primary-bot-message", send_bot_message(uid, primary, response)
            )
        )
        for secondary in secondaries:
            tasks.append(
                atm.create_task(
                    "send-secondary-not-message",
                    send_preparing_response_message(
                        secondary.name, secondary.initial_greeting
                    ),
                )
            )
            await comment(icm, uid, secondary, span)
    except QuotaExceededError as e:
        await handle_quota_exceeded(uid, e, span)
    finally:
        for result in await asyncio.gather(*tasks, return_exceptions=True):
            if isinstance(result, Exception):
                current_app.logger.exception(result)


async def comment(icm: InquiryContextManager, uid: str, persona: Persona, span: Span):
    """
    Request a chatbot persona to comment on the current chat history
    :param uid: Unique identifier of the requesting message
    :param icm: Inquire context manager for the conversation
    :param persona: Persona you wish to have comment
    :param span: Tracing span for tracing and debugging
    """
    try:
        response: InquiryResponse = await icm.comment_on_history(persona)
        span.set_attribute(f"response.{persona.prompt_name}", response.message)
        await send_bot_message(uid, persona, response)
    except QuotaExceededError as e:
        await handle_quota_exceeded(uid, e, span)


async def send_system_message(uid: str, message: str):
    """
    Send a system message to the current websocket
    :param uid: Unique identifier of the message associated with the system message
    :param message: Message to send
    :return: None
    """
    message = json.dumps(
        {
            "id": uid,
            "type": "system-message",
            "text": message,
        }
    )
    await websocket.send(message)


async def send_bot_message(uid: str, sender: Persona, message: InquiryResponse):
    """
    Send a message from a chatbot persona
    :param uid: Unique identifier of origination message
    :param sender: Chatbot persona name
    :param message: Message to send
    :return: None
    """
    ws_message = json.dumps(
        {
            "id": uid,
            "type": "bot-message",
            "from": sender.name,
            "avatar": url_for("static", filename=sender.avatar_file),
            "text": message.message,
            "data": [
                {
                    "content": item.data,
                    "type": item.type.value,
                    "encoding": item.encoding,
                    "mimeType": item.mime_type,
                }
                for item in message.data
            ],
        }
    )
    await websocket.send(ws_message)


async def send_preparing_response_message(sender: str, greeting: str):
    """
    Alert the websocket client that a chatbot persona is preparing a response
    :param sender: Chatbot persona which is preparing a response
    :param greeting: Chatbot persona's greeting message
    """
    message = json.dumps(
        {
            "type": "preparing-response",
            "greeting": greeting,
            "from": sender,
        }
    )
    await websocket.send(message)


async def send_experts_message(count: int):
    """
    Send a list of experts in a message to the websocket client
    :param count: How many personas to send messages from
    """
    featured_personas = [persona for persona in PERSONAS if persona.is_promoted_persona]

    other_personas = [
        persona for persona in PERSONAS if not persona.is_promoted_persona
    ]

    experts = []
    for i in range(count):
        if featured_personas:
            random.shuffle(featured_personas)
            persona = featured_personas.pop()
        else:
            random.shuffle(other_personas)
            persona = other_personas.pop()
        experts.append({"name": persona.name, "greeting": persona.initial_greeting})

    random.shuffle(experts)
    message = json.dumps(
        {
            "type": "experts-list",
            "experts": experts,
        }
    )

    await websocket.send(message)


async def handle_quota_exceeded(uid: str, e: QuotaExceededError, span: Span):
    """
    Handle the raising of a quota exceeded error
    :param uid: Unique identifier of the associated message
    :param e: Error raised
    :param span: Tracing span for tracing and debugging
    """
    current_app.logger.info(f"Quota exceeded error: {e}")
    response = "Unfortunately, our experts have answered all the questions "
    "they will answer for today. Please try again tomorrow."
    span.set_attribute("response.system", response)
    await send_system_message(uid, response)


async def add_messages_to_history(
    icm: InquiryContextManager, messages: list[tuple[str, str]]
):
    """
    Add messages to the session history. This is often used to resume a conversation.
    :param icm: Inquiry context manager for the session
    :param messages: List of tuples of message "from" and "text" pairs to add to the history
    """
    for from_, text in messages:
        icm.prepend_history(from_, text)


async def send_error_message(uid: str, message: str):
    """
    Send an error message to the websocket
    :param uid: Unique identifier of the message being processed when the error occurred
    :param message: Error message to send
    :return: None
    """
    message = json.dumps(
        {
            "type": "error",
            "text": message,
        }
    )
    await websocket.send(message)
