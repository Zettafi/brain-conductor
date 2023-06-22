import logging
from base64 import encodebytes
from dataclasses import dataclass
from typing import Optional
from random import choice
from . import HuggingFace


LOGGER = logging.getLogger("Brain Conductor")


@dataclass
class AIGeneratedImage:
    encoded_image: str
    image_type: str
    image_generation_prompt: str


class StableDiffusion(HuggingFace):
    """Stable Diffusion toolkit"""

    async def _expand_prompt(self, prompt) -> str:
        """
        Expands a simple image request prompt into one that is much more creative and varied.
        :param prompt: The initial prompt
        :return: The expanded prompt
        """
        prompt = f"""I want you to act as a prompt engineer.
        You will help me write prompts for an ai art generator called Stable Diffusion.

        I will provide you with short content ideas and your job is to elaborate
        these into full, explicit, coherent prompts.

        Prompts involve describing the content and style of images in concise accurate language.
        It is useful to be explicit and use references to popular culture, artists and mediums.
        Your focus needs to be on nouns and adjectives. I will give you some example prompts
        for your reference. Please define the exact camera that should be used.

        Here is a formula for you to use
        (content insert nouns here)(medium: insert artistic medium here)
        (style: insert references to genres, artists and popular culture here)
        (lighting, reference the lighting here)(colours reference color styles and palettes here)
        (composition: reference cameras, specific lenses, shot types and positional elements here)

        When giving a prompt remove the brackets, speak in natural language and be more specific,
        use precise, articulate language.

        For your response, simply return the prompt exactly as it will be submitted.

        Example prompt:

        Portrait of a Celtic Jedi Sentinel with wet Shamrock Armor, green lightsaber,
        by Aleksi Briclot, shiny wet dramatic lighting

        Given prompt:
        {prompt}"""
        messages = [
            {"role": "system", "content": prompt},
        ]
        response = await self.llm.chat_complete(messages)
        return response

    async def get_jpeg_image(self, prompt) -> Optional[AIGeneratedImage]:
        """
        Returns a base64 encoded JPEG from a given prompt.
        The received prompt will be expanded upon by asking the classes defined LLM to do so.
        :param prompt: An image generation prompt
        :return: A base64 encoded JPEG string and the expanded prompt that was used to generate it
        """
        LOGGER.debug(f"Image request prompt: {prompt}")
        prompt = await self._expand_prompt(prompt)
        LOGGER.debug(f"Expanded prompt: {prompt}")

        apis = [
            "/models/stabilityai/stable-diffusion-2-1-base",
            "/models/Masagin/Deliberate",  # Character, photorealistic, cinematic
        ]

        response_bytes = await self._query_api(choice(apis), inputs=prompt)
        LOGGER.debug("Image received")
        return (
            AIGeneratedImage(
                encoded_image=encodebytes(response_bytes).decode(),
                image_type="JPEG",
                image_generation_prompt=prompt,
            )
            if response_bytes
            else None
        )
