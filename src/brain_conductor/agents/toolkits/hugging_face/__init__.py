import aiohttp
import logging
import backoff
from aiohttp.client_exceptions import ClientResponseError
from ...llm import LLM

LOGGER = logging.getLogger("Brain Conductor")


class HuggingFace:
    """Hugging Face Base toolkit"""

    def __init__(
        self,
        access_token: str,
        llm: LLM,
        base_url: str = "https://api-inference.huggingface.co",
    ):
        self.access_token = access_token
        self.llm = llm
        self.base_url = base_url
        self.request_headers = {"Authorization": f"Bearer {self.access_token}"}

    @backoff.on_exception(
        backoff.expo, ClientResponseError, max_tries=5, raise_on_giveup=False
    )
    async def _query_api(self, path: str, **kwargs):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}{path}",
                headers=self.request_headers,
                json=kwargs,
            ) as response:
                try:
                    response.raise_for_status()
                    result = await response.read()
                except Exception as e:
                    LOGGER.error(f"Error getting results for {path}: {e}")
                    raise
                return result
