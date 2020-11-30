from flask import Flask, request, g

from redis import Redis
from dotenv import load_dotenv
from bcrypt import hashpw, gensalt, checkpw
from datetime import datetime
from jwt import decode
from uuid import uuid4
import json, os


app = Flask(__name__)
load_dotenv()

cloud_url = os.environ.get("REDIS_URL")
db = Redis.from_url(cloud_url) if cloud_url else Redis(host="redis")

JWT_SECRET = os.getenv("JWT_SECRET")
app.config.from_object(__name__)


@app.route("/login", methods=["GET"])
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

@app.route("/sender/<username>/packages", methods=["GET"])
def get_sender_packages(username):
    package_names = db.smembers(f"user_packages:{username}")

    packages = []
    for name in package_names:
        byte_package = db.hgetall(name).items()
        package = {key.decode(): value.decode() for key, value in byte_package}
        package["id"] = name.decode().replace("package:", "")
        packages.append(package)

    packages = sorted(packages, key=lambda k: int(k["box_id"]))
    return {"packages": packages}, 200

@app.route("/sender/<username>/packages", methods=["POST"])
def add_sender_package(username):
    json = request.json
    print(json, flush=True)

    id = uuid4()
    db.hset(f"package:{id}", "recipient", json["recipient"])
    db.hset(f"package:{id}", "box_id", json["box_id"])
    db.hset(f"package:{id}", "size", json["size"])
    db.hset(f"package:{id}", "status", "label")
    db.sadd(f"user_packages:{username}", f"package:{id}")

    return {"package_id": id}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
