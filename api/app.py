from flask import Flask, request, g

from redis import Redis
from dotenv import load_dotenv
from bcrypt import hashpw, gensalt, checkpw
from datetime import datetime
import os
from jwt import decode
import json


app = Flask(__name__)
load_dotenv()

cloud_url = os.environ.get("REDIS_URL")
db = Redis.from_url(cloud_url) if cloud_url else Redis(host="redis")

JWT_SECRET = os.getenv("JWT_SECRET")
app.config.from_object(__name__)

@app.route("/login", methods=["POST"])
def login():
    print(request.json, flush=True)
    json = request.json

    if not json:
        return {"error": "No JSON provided"}, 400

    username = json.get("username")
    password = json.get("password")

    db_password = db.hget(f"user:{username}", "password")

    if not db_password:
        return {"error": "Invalid username"}, 400
    if not checkpw(password.encode(), db_password):
        return {"error": "Invalid password"}, 400

    return {"status": "logged-in"}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
