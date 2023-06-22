"""
Module containing chatbot agent logic
"""
import abc
import logging
from inspect import getmembers
from json import loads
from json.decoder import JSONDecodeError
from string import Template
from typing import List
from dataclasses import dataclass
from .llm.openai import OpenAI
from .toolkits import ToolResponseType
from .toolkits.hugging_face.stable_diffusion import AIGeneratedImage

from .toolkits import (
    Tool,
    ToolKit,
)

LOGGER = logging.getLogger("Brain Conductor")


@dataclass
class AgentResponse:
    response: str
    images: List[str]


class Agent(abc.ABC):
    """
    Abstract base class for chatbot agents
    """

    def __init__(self, tool_kits: List[ToolKit], max_retries: int = 5):
        self._tool_kits = tool_kits
        self._max_retries = max_retries
        available_methods = self.__build_available_methods_based_on_toolkits()
        self.toolkit_query_template = Template(
            self.toolkit_query_template.substitute(available_methods=available_methods)
        )

    llm = OpenAI()
    toolkit_query_template = Template(
        """Considering the previous messages and the last message from the user.

    In order to obtain more context you have access to methods with their name,
    whether they are required and should always be used, their variables, and
    description listed in the following format.

    Method Name : Required : Input variable 1, Input variable 2 : Description

    Review the methods you have access to below:

    BEGIN CALLABLE METHODS

    $available_methods

    END CALLABLE METHODS

    Considering the methods you have access to, and remembering that some
    methods may be marked as required, please list any that would provide you
    with useful information to reply to the previous message. Reply only in the
    following format with nothing before or after it. Do not include any words at all
     and just include the format given:
    [
        {
            "method": "Method Name 1",
            "args": ["Input Variable 1"]
        },
        {
            "method": "Method Name 2",
            "args": ["Input Variable 3", "Input Variable 4"]
        },
        {
            "method": "Method Name 3",
            "args": ["Input Variable 5", "Input Variable 6"]
        }
    ]

    Be sure to use double quotes not single.

    If a method is marked as required you must always call this method with no exception.

    Do not request input from the user or attempt to use any methods that do not exist."""
    )

    response_template = Template(
        """Below are the results of you running processes based on the user's previous message.
    Assume any data you are receiving is up to date as of today.
    Use your existing knowledge and data as supplementary material when responding.
    Do not reference data being visible to the user as they do not know it exists.
    Keep your personality in mind and strongly use it in wording your response.
    If the information is not relevant to the conversation either don't use it,
    or use it sparingly as to not confuse the user. IE don't randomly talk about the price
    of bitcoin when someone is asking about buying a house.
    If data you have has already been explained or referenced by yourself or another expert, don't
    repeat that information.
    Make a strong effort to keep on topic by viewing the user's previous messages, and also take the
    other experts responses into secondary account.

    Results:
    $data"""
    )

    @staticmethod
    def __build_method_description_from_toolkit(toolkit: ToolKit) -> str:
        description = ""
        for name, obj in getmembers(toolkit):
            if isinstance(obj, Tool):
                description += (
                    f"{toolkit.prefix}.{name} : "
                    f"{obj.required} : "
                    f"{', '.join(obj.args)}\n : "
                    f"{obj.description}\n\n"
                )
        return description

    def __build_available_methods_based_on_toolkits(self) -> str:
        available_methods = ""
        for kit in self._tool_kits:
            available_methods += self.__build_method_description_from_toolkit(kit)
        return available_methods

    async def process_messages(self, messages: List[dict]) -> AgentResponse:
        """
        Process messages and return a response from the agent
        :param messages: List of messages
        :return: Agent response
        """
        choice_messages = [
            message for message in messages if message["role"] != "system"
        ]
        choice_messages.append(
            {
                "role": "system",
                "content": self.toolkit_query_template.substitute(),
            }
        )

        methods = await self.llm.chat_complete(choice_messages, temperature=1)
        data = ""
        images = []
        try:
            loaded_methods = loads(methods.strip())
            LOGGER.info(f"Parsed the following methods: {methods}")
        except JSONDecodeError:
            LOGGER.error(f"Failed to parse methods from: {methods}")
            loaded_methods = []

        for item in loaded_methods:
            try:
                prefix, method = item["method"].split(".")
            except (ValueError, KeyError):
                LOGGER.error(f"Failed to split on method: {item['method']}")
                continue

            pending_data = []
            pending_images = []
            for toolkit in self._tool_kits:
                if toolkit.prefix == prefix and hasattr(toolkit, method):
                    LOGGER.info(f"Retrieving: {prefix}.{method}")
                    to_call = getattr(toolkit, method)
                    if item.get("args"):
                        pending = to_call(*item["args"])
                    else:
                        pending = to_call()

                    if to_call.response_type == ToolResponseType.DATA:
                        pending_data.append(pending)
                    elif to_call.response_type == ToolResponseType.IMAGE:
                        pending_images.append(pending)
            for response in pending_data:
                data += await response + "\n" if response else ""
            for response in pending_images:
                image: AIGeneratedImage = await response
                if image:
                    images.append(image.encoded_image)
                    data += (
                        f"You have generated an image with the following description:\n "
                        f"{image.image_generation_prompt}\n\nNote that this"
                        f"description was made by you based on the user's previous input."
                        f"They did not give this exact request"
                    )
                else:
                    data += (
                        "You tried to generate an image but experienced technical difficulties."
                        "Let the user know of this."
                    )
            LOGGER.debug(f"Retrieved Data: {data}")
        if not data:
            data = (
                "You did not retrieve any data. Please just respond to the question with "
                "your own personality and knowledge."
            )
        message = {
            "role": "system",
            "content": self.response_template.substitute(data=data),
        }

        response = await self.llm.chat_complete(messages + [message])
        return AgentResponse(response=response, images=images)


class CryptoAgent(Agent):
    """
    Agent implementation for enriching chatbots with cryptocurrency literacy
    """

    def __init__(self, crypto_toolkit, time_toolkit):
        self.toolkit_query_template = Template(
            """You are a CryptoCurrency expert and have access to some external tools
            in order to help you respond to questions and provide input.

            You will be looking at the available methods you have and returning
            a machine readable format which will immediately be parsed and used
            to provide additional data to you in order to provide a better response.

            Please review the previous messages and the last message from the user.

            You have access to methods in the following format.

            Method Name : Required : Input variable 1, Input variable 2 : Description

            Review the methods you have access to below:

            BEGIN CALLABLE METHODS

            $available_methods

            END CALLABLE METHODS

            First strongly consider the previous messages in the conversation in order to obtain
            context of what you may need more information for.

            Now considering the methods you have access to, and being aware that these methods
            may not always be relevant are are thus not always required.

            Reply only in the following format (JSON):
            [
                {
                    "method": "Method Name 1",
                    "args": ["Input Variable 1"]
                },
                {
                    "method": "Method Name 2",
                    "args": ["Input Variable 3", "Input Variable 4"]
                },
                {
                    "method": "Method Name 3",
                    "args": ["Input Variable 5", "Input Variable 6"]
                }
            ]

            Be sure to use double quotes not single.

            Do not request input from the user or attempt to use any methods that do not exist.

            If you do not identify any methods that are useful,
            just respond with an empty JSON list. So:
            []

            You are returning your response to be parsed by software.

            Do not include any other information in your response that
            is not the requested JSON above as it will not be seen by
            the user or anyone else.

            It is not your job right now to provide direct input for the topic
            at hand. Your job is to simply identify if the methods available
            will be beneficial in order to develop an answer in the future.
            """
        )

        self.response_template = Template(
            self.response_template.safe_substitute()
            + "\n\nWhen you are giving numbers please round to the nearest cent and "
            "include commas or turn large number an abbreviated form (IE: "
            "10k, 26 thousand dollars, 2.1 billion, etc).\nFinally above all things. Your"
            "goal is to contribute to the conversation in a meaningful way. If the "
            "conversation is not related to Crypto. Do not start listing prices"
            "and derail the conversation as the user will not be happy. The data"
            "you received may not always be relevant or even useful for the "
            "conversation. Also be aware that others may have access to the same"
            "data and have already listed it. Don't repeat the same information "
            "if another expert already has. Duplicate information that has already "
            "been stated is not acceptable."
        )

        super().__init__([crypto_toolkit, time_toolkit])


class ArtAgent(Agent):
    def __init__(self, art_toolkit):
        self.toolkit_query_template = Template(
            """Considering the previous messages and the last message from the user.

            You are a seasoned artist and will be generating a piece of artwork based
            on the user's previous message or messages. You will be generating a prompt
            that will be sent to generative art software. Generate a prompt that best
            describes what the user is requesting, or something that describes what a
            logic response would be to their question if they are not explicitly requesting
            art to be generated. You must always generate a piece of art with no exceptions.

            Below is the format of what the available methods you have and how they will be
            presented.

            Method Name : Required : Input variable 1, Input variable 2 : Description

            Review the methods you have access to below:

            BEGIN CALLABLE METHODS

            $available_methods

            END CALLABLE METHODS

            For your response. List the method or methods you will be calling exactly in
            the following format (JSON):

            [
                {
                    "method": "Method Name 1",
                    "args": ["Image generation prompt"]
                }
            ]

            An example would be:

            [
                {
                    "method": "art.generate_art",
                    "args": ["Two golden retrievers playing in the park"]
                }
            ]

            Be sure to use double quotes not single.

            Do not request input from the user or attempt to use any methods that do not exist.
            You must always generate art and do not have access to user input so must come up
            with a value that works best.

            Only return the requested JSON as the response you return will be directly parsed
            by software and not seen by anyone else."""
        )
        self.response_template = Template(
            """You are an artist that has access to tools to generate digital art.
            In response to the users most recent message you have already requested to
            generate a unique piece of artwork. The art itself may have been requested
            by them directly, or you deemed to generate the art as a way to enhance your
            response to them.

            Assuming the artwork was successfully generated you will be displaying the
            image to the user below your response.
            Do not give any links in your response when displaying or describing the
            image as you do not actually have an means to generate links. It will be
            displayed directly to the user.

            Do not say that you will be working on the image as assuming the tool
            was successful it has already been completed and it is ready right now.
            State that it is complete and you are displaying it to them in your response.

            Below you will see the response from the art tool. It wll state whether it was
            successful or failed and the specifications you previously gave it for the image.

            One very important thing to consider is the user's previous statement as they may
            not just be asking you do generate art. If they requested actual input or you are
            contributing to a conversation, don't just describe the art by itself.

            Artwork Generation Tool Response:
            $data"""
        )
        super().__init__([art_toolkit])
