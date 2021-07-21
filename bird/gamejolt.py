import hashlib
import json
import urllib.request
import urllib.error
from urllib.parse import quote

GAME_ID = "294252"
BASE_URL = "https://api.gamejolt.com/api/game/v1_2"


def md5(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def do_request(url):
    try:
        response = urllib.request.urlopen(url)
        data = json.loads(response.read().decode())["response"]
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        return
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")
        return

    if data["success"] != "true":
        print(f"Bad Response: " + data["message"])
        return

    return data


class GameJolt:
    def __init__(self, private_key):
        self.private_key = private_key

    def batch_fetch_url(self, table_ids, limit=10):
        assert len(table_ids) <= 50
        sub_requests = "&".join(self._fetch_subrequest(table_id, limit) for table_id in table_ids)
        url = self._sign(f"{BASE_URL}/batch?game_id={GAME_ID}&{sub_requests}&parallel=true")
        return do_request(url)

    def _fetch_subrequest(self, table_id, limit):
        url = self._sign(f"/scores/?game_id={GAME_ID}&limit={limit}&table_id={table_id}")
        return "requests[]=" + quote(url, safe="")

    def _sign(self, url):
        signature = md5(url + self.private_key)
        return f"{url}&signature={signature}"
