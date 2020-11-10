from flask import Flask, render_template
from flask_session import Session

from redis import Redis
from os import getenv
from dotenv import load_dotenv


db = Redis(host="redis", port=6379, db=0)
load_dotenv()
SESSION_TYPE = "redis"
SESSION_REDIS = db
app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key=getenv("SECRET_KEY")
ses = Session(app)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/sender/sign-up")
def sender_sign_up():
    return render_template("sender_sign_up.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
