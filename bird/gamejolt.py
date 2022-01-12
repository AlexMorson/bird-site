import asyncio
import hashlib
import logging
from typing import Optional
from urllib.parse import quote

from aiohttp import ClientSession
from aiohttp.client_exceptions import ClientError
from pydantic import BaseModel, ValidationError
from yarl import URL

logger = logging.getLogger(__name__)

GAME_ID = "294252"
BASE_URL = "https://api.gamejolt.com/api/game/v1_2"


def md5(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()


class Score(BaseModel):
    extra_data: str
    guest: int
    score: str
    sort: int
    stored: str
    stored_timestamp: int
    user: str
    user_id: str


class Scores(BaseModel):
    message: str = ""
    success: str
    scores: list[Score] = []


class Responses(BaseModel):
    message: str = ""
    success: str
    responses: list[Scores] = []


class Response(BaseModel):
    response: Responses


class GameJoltException(ClientError):
    """Exception raised when a GameJolt request is unsuccessful."""


class GameJolt:
    def __init__(self, private_key: str):
        self._private_key: str = private_key

    async def get_scores(
            self, table_ids: list[int], limit: int = 10, batch_size: int = 32
    ) -> Optional[list[list[Score]]]:
        batches = [table_ids[i:i + batch_size] for i in range(0, len(table_ids), batch_size)]
        urls = [self._full_url(self._batch_scores_url(batch, limit)) for batch in batches]
        async with ClientSession() as session:
            try:
                results = await asyncio.gather(*(self._get_scores(session, url) for url in urls))
            except (ClientError, ValidationError, GameJoltException):
                logger.exception("Could not fetch scores.")
                return None

        return sum(results, [])

    @staticmethod
    async def _get_scores(session: ClientSession, url: str) -> list[list[Score]]:
        logger.debug(f"Fetching url. url={url}")
        async with session.get(URL(url, encoded=True)) as response:
            if not response.ok:
                raise GameJoltException(f"{response.status} {response.reason}")
            data = await response.json()

        responses = Response.parse_obj(data).response
        if responses.success != "true":
            raise GameJoltException(f"Unsuccessful request. message='{responses.message}'")

        all_scores = responses.responses
        for scores in all_scores:
            if scores.success != "true":
                raise GameJoltException(f"Unsuccessful request. message='{scores.message}'")

        return [scores.scores for scores in all_scores]

    def _sign(self, url: str) -> str:
        signature = md5(url + self._private_key)
        return f"{url}&signature={signature}"

    def _full_url(self, relative_url: str) -> str:
        return self._sign(BASE_URL + relative_url)

    def _batch_url(self, url: str) -> str:
        return "requests[]=" + quote(self._sign(url), safe="")

    def _batch_scores_url(self, table_ids: list[int], limit: int) -> str:
        sub_requests = "&".join(
            self._batch_url(self._scores_url(table_id, limit))
            for table_id in table_ids
        )
        return f"/batch?game_id={GAME_ID}&{sub_requests}&parallel=true"

    @staticmethod
    def _scores_url(table_id: int, limit: int) -> str:
        return f"/scores/?game_id={GAME_ID}&limit={limit}&table_id={table_id}"
