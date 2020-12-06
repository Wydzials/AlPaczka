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
db = Redis.from_url(cloud_url) if cloud_url else Redis(host="redis", decode_responses=True)

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
    if not checkpw(password.encode(), db_password.encode()):
        return {"error": "Invalid password"}, 400

    return {"status": "logged-in"}, 200

@app.route("/sender/<username>/packages", methods=["GET"])
def get_sender_packages(username):
    package_names = db.smembers(f"user_packages:{username}")

    packages = []
    for name in package_names:
        package = db.hgetall(name)
        package["id"] = name.replace("package:", "")
        packages.append(package)

    packages = sorted(packages, key=lambda k: int(k["box_id"]))
    return json.dumps(packages), 200

@app.route("/sender/<username>/packages", methods=["POST"])
def add_sender_package(username):
    package = request.json

    id = uuid4()
    db.hset(f"package:{id}", "recipient", package["recipient"])
    db.hset(f"package:{id}", "box_id", package["box_id"])
    db.hset(f"package:{id}", "size", package["size"])
    db.hset(f"package:{id}", "status", "label")
    db.sadd(f"user_packages:{username}", f"package:{id}")

    print("Created package: " + str(db.hgetall(f"package:{id}")) + " from sender " + username, flush=True)
    return json.dumps(db.hgetall(f"package:{id}")), 200

@app.route("/sender/<username>/packages/<id>", methods=["DELETE"])
def delete_sender_package(username, id):
    is_package_sender = db.sismember(f"user_packages:{username}", f"package:{id}")

    if not db.hget(f"package:{id}", "recipient"):
        return {"error": "Not found"}, 400

    if not is_package_sender:
        return {"error": "Unauthorized"}, 401
    
    if not db.hget(f"package:{id}", "status") == "label":
        return {"error": "Package in transit cannot be deleted"}, 400

    db.srem(f"user_packages:{username}", f"package:{id}")
    db.delete(f"package:{id}")

    print("Deleted package: " + id + " from sender: " + username, flush=True)
    return "ok", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
