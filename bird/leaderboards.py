import asyncio
import logging
import sys
import time
from collections import defaultdict
from typing import Optional
from urllib.parse import unquote

import aiosqlite

from bird import gamejolt
from bird.gamejolt import Score
from bird.levels import LEVELS
from bird.queries import (
    COPY_REPLAY_TO_DELETED,
    CREATE_TABLES,
    DELETE_REPLAY,
    INSERT_LEVEL,
    INSERT_USER,
    INSERT_REPLAY,
    JOURNAL_MODE,
    UPDATE_PERSONAL_BESTS,
)

logger = logging.getLogger(__name__)


class Leaderboards:
    def __init__(self, private_key: str):
        self.gamejolt = gamejolt.GameJolt(private_key)

    @staticmethod
    async def initialise():
        logger.info("Initialising the database.")
        async with aiosqlite.connect("leaderboards.sqlite") as db:
            await db.execute(JOURNAL_MODE)
            await db.executescript(CREATE_TABLES)
            await db.executemany(INSERT_LEVEL, LEVELS.items())
            await db.commit()

    @staticmethod
    async def fix():
        logger.info("Recomputing personal bests.")
        async with aiosqlite.connect("leaderboards.sqlite") as db:
            await db.executescript(UPDATE_PERSONAL_BESTS)
            await db.commit()

    @staticmethod
    async def delete(level_id: int, user_id: int, timestamp: int):
        logger.info("Deleting replay.")
        parameters = {"level_id": level_id, "user_id": user_id, "timestamp": timestamp}
        async with aiosqlite.connect("leaderboards.sqlite") as db:
            await db.execute(COPY_REPLAY_TO_DELETED, parameters)
            await db.execute(DELETE_REPLAY, parameters)
            await db.commit()
        logger.warning("You may now need to fix the personal bests.")

    async def update(self):
        start = time.time()

        logger.info("Reading leaderboards.")
        all_scores = await self._read_leaderboards()
        if all_scores is None:
            logger.warning("Could not read leaderboards.")
            return False

        logger.info("Updating database.")
        leaderboards = {level_id: scores for level_id, scores in zip(LEVELS, all_scores)}
        await self._update_database(leaderboards)

        end = time.time()
        logger.info(f"Update took: {end - start:.1f}s")

        return True

    async def _read_leaderboards(self) -> Optional[list[list[Score]]]:
        level_ids = [level_id for level_id, name in LEVELS.items() if "Any%" in name or "100%" in name]
        return await self.gamejolt.get_scores(level_ids, 100)

    @staticmethod
    async def _update_database(leaderboards: dict[int, list[Score]]):
        users: defaultdict[int, tuple[int, str]] = defaultdict(lambda: (0, ""))
        replays = []
        for level_id, scores in leaderboards.items():
            for score in scores:
                user_name, replay = unquote(score.extra_data).split(";")[:2]
                frame_count = score.sort
                user_id = score.guest
                timestamp = score.stored_timestamp
                if users[user_id][0] < timestamp:
                    users[user_id] = (timestamp, user_name)
                replays.append((level_id, user_id, timestamp, frame_count, replay))

        async with aiosqlite.connect("leaderboards.sqlite") as db:
            await db.executemany(
                INSERT_USER,
                [(user_id, user_name) for user_id, (timestamp, user_name) in users.items()]
            )
            await db.executemany(INSERT_REPLAY, replays)
            await db.commit()


async def main():
    import argparse
    import os

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(required=True, dest="command")

    subparsers.add_parser("init", help="Initialise the database")
    subparsers.add_parser("fix", help="Recompute personal bests")
    subparsers.add_parser("update", help="Update the leaderboards")

    delete_parser = subparsers.add_parser("delete", help="Delete a replay")
    delete_parser.add_argument("level_id", type=int)
    delete_parser.add_argument("user_id", type=int)
    delete_parser.add_argument("timestamp", type=int)

    args = parser.parse_args()

    if args.command == "init":
        await Leaderboards.initialise()

    if args.command == "fix":
        await Leaderboards.fix()

    if args.command == "update":
        private_key = os.environ.get("PRIVATE_KEY")
        if private_key is None:
            logger.error("No private key provided")
            return
        lb = Leaderboards(private_key)
        if not await lb.update():
            sys.exit(1)

    if args.command == "delete":
        await Leaderboards.delete(args.level_id, args.user_id, args.timestamp)


if __name__ == "__main__":
    asyncio.run(main())
