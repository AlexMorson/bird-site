import os

from flask import Flask

from bird import leaderboards

app = Flask(__name__)
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

private_key = os.environ.get("PRIVATE_KEY")
if private_key is None:
    raise RuntimeError("No private key provided")

lb = leaderboards.LeaderboardReader(private_key)
lb.start()

from bird import routes
