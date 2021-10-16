from flask import Flask

app = Flask(__name__)
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

from bird import routes

if __name__ == "__main__":
    app.run()
