import datetime
import sqlite3
import threading
import time
from urllib.parse import unquote

from bird import gamejolt
from bird.levels import LEVELS
from bird.queries import CREATE_TABLES, INSERT_LEVEL, INSERT_USER, INSERT_REPLAY, UPDATE_PERSONAL_BESTS


class LeaderboardReader(threading.Thread):
    def __init__(self, private_key):
        super().__init__()
        self.gamejolt = gamejolt.GameJolt(private_key)
        self.conn = None
        self.c = None

    def run(self):
        self._init_database()
        self._update_every_hour()

    def _init_database(self):
        self.conn = sqlite3.connect("leaderboards.sqlite")
        self.c = self.conn.cursor()

        self.c.executescript(CREATE_TABLES)
        self.c.executemany(INSERT_LEVEL, LEVELS.items())
        self.conn.commit()

    def _update_every_hour(self):
        while True:
            now = datetime.datetime.now()
            next_hour = now.replace(microsecond=0, second=0, minute=0) + datetime.timedelta(hours=1)
            seconds_to_wait = (next_hour - now).total_seconds()
            time.sleep(seconds_to_wait)
            self._update()

    def _update(self):
        print("Updating...")
        start = time.time()
        leaderboards = self._read_leaderboards()
        if leaderboards is None:
            print("Could not read leaderboards")
            return
        values = {level_id: response["scores"] for
                  level_id, response in zip(LEVELS, leaderboards) if
                  response["success"] == "true"}
        self._update_database(values)
        end = time.time()
        print(f"Update took: {end - start:.1f}s")

    def _read_leaderboards(self):
        level_ids = [level_id for level_id, name in LEVELS.items() if "Any%" in name or "100%" in name]
        batch_size = 32  # Fits everything into 4 requests
        level_id_groups = [level_ids[i:i + batch_size] for i in range(0, len(level_ids), batch_size)]
        responses = []
        for level_id_group in level_id_groups:
            data = self.gamejolt.batch_fetch_url(level_id_group, 100)
            if data is None:
                return
            responses.extend(data["responses"])
        return responses

    def _update_database(self, values):
        users = []
        replays = []
        for level_id, scores in values.items():
            for score in scores:
                user_name, replay = unquote(score["extra_data"]).split(";")[:2]
                frame_count = score["sort"]
                user_id = score["guest"]
                timestamp = score["stored_timestamp"]
                users.append((user_id, user_name))
                replays.append((level_id, user_id, timestamp, frame_count, replay))
        self.c.executemany(INSERT_USER, users)
        self.c.executemany(INSERT_REPLAY, replays)
        self.c.execute(UPDATE_PERSONAL_BESTS)
        self.conn.commit()
