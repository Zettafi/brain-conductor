"""
Toolkit package which houses tools and the toolkits that house them
"""
from abc import ABC
from dataclasses import dataclass
from typing import List, Callable
from enum import Enum
from .coinmarketcap import CoinMarketCap
from .hugging_face.stable_diffusion import StableDiffusion
from .dates import Dates


class ToolResponseType(Enum):
    """
    Enum for determining what response format a tool is expected to return.
    """

    DATA = "1"
    IMAGE = "2"


@dataclass
class Tool:
    """
    Tool definition
    """

    args: List[str]
    method: Callable
    description: str
    response_type: ToolResponseType = ToolResponseType.DATA
    required: bool = False

    async def __call__(self, *args, **kwargs):
        return await self.method(*args, **kwargs)


class ToolKit(ABC):
    """
    Toolkit base class. Toolkits house and provide tools
    """

    prefix: str


class CryptoToolkit(ToolKit):
    """
    Crypto toolkit for access to cryptocurrency-based tools
    """

    prefix = "crypto"

    def __init__(self, coin_market_cap_extension: CoinMarketCap) -> None:
        self._coin_market_cap_extension = coin_market_cap_extension

    @property
    def get_current_usd_price(self):
        """
        :return: Get current USD price tool
        """
        return Tool(
            args=["token_symbol"],
            method=self._coin_market_cap_extension.get_current_usd_price,
            description="Retrieves the current price of a cryptocurrency by its symbol "
            "in USD. IE: eth, btc, ltc, doge",
        )

    @property
    def get_coin_summary(self):
        """
        :return: Get coin summary tool
        """
        return Tool(
            args=["token_symbol"],
            method=self._coin_market_cap_extension.get_coin_summary,
            description="Retrieves the current summary of a given cryptocurrency "
            "including its pricing information. This includes its volume, current price data, "
            "as well as price change over the last 1 hour, 24 hours, or 7 days.",
        )

    @property
    def get_current_top_coins_by_volume(self):
        """
        :return: Get current top coins by volume tool
        """
        return Tool(
            args=["count"],
            method=self._coin_market_cap_extension.get_current_top_coins_by_volume,
            description="Retrieves the top cryptocurrency by their volume in the last 24 hours, "
            "with count being how many to retrieve from the top x coins. This includes "
            "their volume, current price data, as well as price change over the last "
            "1 hour, 24 hours, or 7 days.",
        )

    # Not allowed for free plan
    # @property
    # def get_trending_coins_based_on_gains_and_losses(self):
    #     return Tool(
    #         args=["count"],
    #         method=self._coin_market_cap_extension.get_trending_coins,
    #         description="Retrieves a list of trending coins who are either "
    #                     "the biggest winners of losers for the day, with "
    #                     "count being how many coins to retrieve."
    #     )


class TimeToolKit(ToolKit):
    """
    Toolkit for access to current date
    """

    prefix = "time"

    def __init__(self, date_extension: Dates) -> None:
        self._date_extension = date_extension

    @property
    def get_current_date(self):
        """
        :return: Get current date tool
        """
        return Tool(
            args=[],
            method=self._date_extension.get_current_date,
            description="Retrieves the current date. There are no input variables.",
        )


class ArtToolKit(ToolKit):
    prefix = "art"

    def __init__(self, stable_diffusion_extension: StableDiffusion) -> None:
        self._stable_diffusion_extension = stable_diffusion_extension

    @property
    def generate_art(self):
        """
        :return: Generate art tool
        """
        return Tool(
            args=["image_prompt"],
            method=self._stable_diffusion_extension.get_jpeg_image,
            description="Retrieves a dynamically generated image."
            "image_prompt is an input given that will return an image "
            "best displaying the text given."
            'The image prompt value will never simply be "image_prompt" '
            "it will be based on the text the user provides. "
            "If they are not requesting a piece of art specifically, "
            "come up with a prompt yourself on something interesting "
            "that relates to the user input and will enhance your response to them. "
            "Such as if they are talking about improving in art, submit an "
            'image_prompt of "art supplies". If they ask you how you are doing '
            'request a "sunrise". This method is required. Always call it.',
            response_type=ToolResponseType.IMAGE,
            required=True,
        )
