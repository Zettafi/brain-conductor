"""LLM Package for all things LLM"""
from abc import ABC, abstractmethod
from typing import List


class LLM(ABC):
    """
    Base class for defining LLM implementations
    """

    def __init__(self, chat_completion_model, text_completion_model):
        self.chat_completion_model = chat_completion_model
        self.text_completion_model = text_completion_model

    @abstractmethod
    async def chat_complete(self, messages: List[dict], **kwargs) -> str:
        """
        Perform chat completion on the provided messaged ad arguments
        :param messages: List of messages to complete
        :param kwargs: Additional information
        :return: LLM response
        """
        raise NotImplementedError

    @abstractmethod
    async def text_complete(self, prompt: str, **kwargs) -> str:
        """
        Perform a text completion on the provided prompt
        :param prompt: Prompt to complete
        :param kwargs: Additional information
        :return: LLM response
        """
        raise NotImplementedError
