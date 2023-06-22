"""OpenAI LLM module"""
import logging
from typing import List
import openai
import backoff
from ...errors import RecoverableError, RateLimitError
from . import LLM


LOGGER = logging.getLogger("Brain Conductor")


class OpenAI(LLM):
    """OpenAI LLM implementation"""

    def __init__(
        self,
        chat_completion_model="gpt-3.5-turbo",
        text_completion_model="text-davinci-003",
    ):
        super().__init__(chat_completion_model, text_completion_model)

    @backoff.on_exception(backoff.expo, RecoverableError)
    async def chat_complete(self, messages: List[dict], **kwargs) -> str:
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.chat_completion_model, messages=messages, **kwargs
            )
        except openai.error.RateLimitError as e:
            LOGGER.debug(f"Chat complete rate limited: {e}")
            raise RateLimitError()

        return response.choices[0].message.content

    @backoff.on_exception(backoff.expo, RecoverableError)
    async def text_complete(self, prompt: str, **kwargs) -> str:
        try:
            response = await openai.Completion.acreate(
                model=self.text_completion_model, prompt=prompt, **kwargs
            )
        except openai.error.RateLimitError as e:
            LOGGER.debug(f"Text complete rate limited: {e}")
            raise RateLimitError()
        return response.choices[0].text
