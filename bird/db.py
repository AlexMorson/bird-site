import sqlite3

from flask import g

from bird.wsgi import app
from bird.queries import JOURNAL_MODE


def get_db():
    if "conn" not in g:
        g.conn = sqlite3.connect("leaderboards.sqlite")
        g.conn.execute(JOURNAL_MODE)
    return g.conn


def get_db_cursor():
    if "c" not in g:
        g.c = get_db().cursor()
    return g.c


@app.teardown_appcontext
def close_db(exception):
    if "c" in g:
        g.c.close()
        del g.c
    if "conn" in g:
        g.conn.close()
        del g.conn
