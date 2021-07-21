import sqlite3

from flask import g

from bird import app


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect("leaderboards.sqlite")
    return g.db


def get_db_cursor():
    db = get_db()
    return db.cursor()


@app.teardown_appcontext
def close_db(exception):
    if "db" in g:
        g.db.close()
