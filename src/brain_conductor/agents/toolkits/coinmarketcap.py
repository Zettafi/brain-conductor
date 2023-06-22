"""Coin Market Cap toolkit module"""
import logging
import aiohttp

LOGGER = logging.getLogger("Brain Conductor")


class CoinMarketCap:
    """Coin Market Cap toolkit"""

    def __init__(
        self, api_key: str, base_url: str = "https://pro-api.coinmarketcap.com"
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.request_headers = {
            "X-CMC_PRO_API_KEY": api_key,
            "Accept": "application/json",
        }

    async def _query_api(self, path: str, **kwargs):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}{path}",
                headers=self.request_headers,
                params=kwargs,
            ) as response:
                try:
                    response.raise_for_status()
                    content = await response.json()
                    results = content["data"]
                except Exception as e:
                    LOGGER.error(f"Error getting results for {path}: {e}")
                    results = list()
                return results

    async def _get_current_quote(
        self, symbol: str | None = None, slug: str | None = None
    ) -> dict:
        params = {}
        if symbol:
            params["symbol"] = symbol.upper()
        if slug:
            params["slug"] = slug

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/v2/cryptocurrency/quotes/latest",
                headers=self.request_headers,
                params=params,
            ) as response:
                try:
                    response.raise_for_status()
                    content = await response.json()
                    data = content["data"]
                    # There should always be a single item in the dict so just
                    # retrieve the first key and return it
                    data_key = list(data.keys())[0]
                    result = (
                        data[data_key][0]
                        if isinstance(data[data_key], list)
                        else data[data_key]
                    )
                except IndexError:
                    LOGGER.error(f"Failed to parse quote response data: {data}")
                    result = dict()
                except Exception as e:
                    LOGGER.error(f"Error getting latest listings: {e}")
                    result = dict()
                return result

    @staticmethod
    def _strip_response_dict(item: dict) -> dict:
        return {
            "name": item["name"],
            "symbol": item["symbol"],
            "max_supply": item["max_supply"],
            "circulating_supply": item["circulating_supply"],
            "total_supply": item["total_supply"],
            "infinite_supply": item["infinite_supply"],
            "quote": {"USD": item["quote"]["USD"]},
        }

    @staticmethod
    def _get_quote_price_summary(quote):
        usd = quote["USD"]
        response = (
            f"Current price: ${usd['price']}\n"
            f"24 hour volume: ${usd['volume_24h']}\n"
            f"1 hour price percent change: {usd['percent_change_1h']}%\n"
            f"24 hour price percent change: {usd['percent_change_24h']}%\n"
            f"7 day price percent change: {usd['percent_change_7d']}%\n"
            f"Market Cap: ${usd['market_cap']}\n"
        )
        if usd.get("market_cap_dominance"):
            response += f"Market Cap Dominance: {usd['market_cap_dominance']}\n"
        return response

    async def get_current_top_coins_by_volume(self, count: int) -> str:
        """
        Get the top n coins by volume
        :param count: Number of coins to retrieve
        :return: A textual representation for use by LLMs in completion requests
        """
        # In order to work around stablecoins we need to pull extras and remove them
        listings = await self._query_api(
            "/v1/cryptocurrency/listings/latest",
            limit=int(count) + 10,
            sort="volume_24h",
        )

        # Compile a list of non-stable coins
        amount_parsed = 0
        parsed_listings = []
        for listing in listings:
            if "stablecoin" not in listing["tags"]:
                amount_parsed += 1
                parsed_listings.append(listing)
            if amount_parsed == count:
                break

        response = f"The following are the top {count} coins in the last 24 hours:\n\n"
        for listing in parsed_listings:
            response += (
                f"{listing['name']} - Symbol: {listing['symbol']}, "
                f"{self._get_quote_price_summary(listing['quote'])}\n\n"
            )
        return response

    async def get_current_usd_price(self, symbol: str) -> str:
        """
        Get the current price of a coin in US Dollars
        :param symbol: Coin to retrieve
        :return: A textual representation for use by LLMs in completion requests
        """
        listing = await self._get_current_quote(symbol=symbol)
        if listing:
            price = f"{listing['quote']['USD']['price']}"
            response = f"The current price of {symbol} is ${price}\n"
        else:
            response = f"Couldn't find a price for {symbol}"
        return response

    async def get_coin_summary(self, symbol: str) -> str:
        """
        Get a summary of a coin
        :param symbol: Coin to summarize
        :return: A textual representation for use by LLMs in completion requests
        """

        listing = await self._get_current_quote(symbol=symbol)
        if listing:
            return (
                f"The current data on {symbol} is:\n"
                f"Name: {listing['name']}\n"
                f"{self._get_quote_price_summary(listing['quote'])}\n"
            )
        else:
            return ""

    async def get_trending_coins(self, count: int) -> str:
        """
        Get the top N trending coins
        :param count: Number of coins to retrieve
        :return: A textual representation for use by LLMs in completion requests
        """

        listings = await self._query_api(
            "/v1/cryptocurrency/trending/gainers-losers", limit=count
        )
        response = (
            "Below is a list of coins that are trending due to a "
            "large gain or loss in value:\n\n"
        )
        for listing in listings:
            response += (
                f"{listing['name']} - Symbol: {listing['symbol']}, "
                f"{self._get_quote_price_summary(listing['quote'])}\n\n"
            )
        return response
