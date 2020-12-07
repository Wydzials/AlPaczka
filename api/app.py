from flask import Flask, request, g

from flask_hal import HAL
from flask_hal.document import Document, Embedded
from flask_hal.link import Link

from redis import Redis
from dotenv import load_dotenv
from bcrypt import hashpw, gensalt, checkpw
from datetime import datetime, timedelta
from jwt import encode, decode, ExpiredSignatureError
from uuid import uuid4
import json, os


app = Flask(__name__)
HAL(app)
load_dotenv()

cloud_url = os.environ.get("REDIS_URL")
db = Redis.from_url(cloud_url) if cloud_url else Redis(host="redis", decode_responses=True)

JWT_SECRET = os.getenv("JWT_SECRET")
app.config.from_object(__name__)

JWT_LIFETIME = 300

@app.before_request
def before():
    token = request.headers.get('Authorization', "").replace('Bearer ','')
    try:
        authorization = decode(token, str(JWT_SECRET), algorithms=['HS256'])
        g.username = authorization.get("sub")
        log('Authorized: ' + g.username)
    except ExpiredSignatureError:
        if request.path != "/login":
            log("Expired token for path: " + request.path)

            links = []
            links.append(Link("login", "/login"))
            data = {"error": "Expired token",
                    "error_pl": "Token wygasł, zaloguj się ponownie."}
            document = Document(data=data, links=links)
            return document.to_json(), 401
    except Exception as e:
        log('Unauthorized: ' + str(e))
        g.username = ""

@app.route("/login", methods=["GET"])
def login():
    json = request.json

    if not json:
        return {"error": "No JSON provided"}, 400

    username = json.get("username")
    password = json.get("password")
    db_password = db.hget(f"user:{username}", "password")

    if not username:
        return {"error": "No username provided", 
                "error_pl": "Nazwa użytkownika nie może być pusta."}, 400

    if not password:
        return {"error": "No password provided", 
                "error_pl": "Hasło nie może być puste."}, 400

    if not db_password:
        return {"error": "Invalid username", 
                "error_pl": "Nieprawidłowa nazwa użytkownika."}, 400

    if not checkpw(password.encode(), db_password.encode()):
        return {"error": "Invalid password", 
                "error_pl": "Nieprawidłowe hasło."}, 400

    log("Logged in user " + username)

    payload = {
        'exp': datetime.utcnow() + timedelta(seconds=JWT_LIFETIME),
        'iat': datetime.utcnow(),
        'sub': username
    }
    token = encode(payload, str(app.config.get("JWT_SECRET")), algorithm="HS256")

    links = []
    links.append(Link("sender:dashboard", "/sender/dashboard"))
    links.append(Link("sender:logout", "/sender/logout"))

    document = Document(data={"status": "logged-in", "token": token.decode()}, links=links)
    return document.to_json()

@app.route("/sender/<username>/packages", methods=["GET"])
def get_sender_packages(username):
    if username != g.get("username"):
        return error("Unauthorized", "Brak dostępu.")

    package_names = db.smembers(f"user_packages:{username}")
    packages = []
    for name in package_names:
        package = db.hgetall(name)
        package["id"] = name.replace("package:", "")
        packages.append(package)

    packages = sorted(packages, key=lambda k: int(k["box_id"]))

    links = []
    links.append(Link("package:create", "/sender/" + g.username + "/packages"))
    links.append(Link("package:delete", "/sender/" + g.username + "/packages/{id}", templated=True))

    document = Document(data={"packages": packages}, links=links)
    return document.to_json()

@app.route("/sender/<username>/packages", methods=["POST"])
def add_sender_package(username):
    if username != g.get("username"):
        return error("Unauthorized", "Brak dostępu.")
    
    package = request.json

    if not package.get("recipient"):
        return error("No recipient provided", "Nazwa adresata nie może być pusta.")
    
    if not package.get("box_id"):
        return error("No box_id provided", "Numer skrytki nie może być pusty.")
    
    try:
        box_id = int(package.get("box_id"))
    except ValueError:
        return error("Invalid box_id", "Nieprawidłowy numer skrytki.")

    if not package.get("size"):
        return error("No size provided", "Rozmiar nie może być pusty.")

    id = uuid4()
    db.hset(f"package:{id}", "recipient", package["recipient"])
    db.hset(f"package:{id}", "box_id", box_id)
    db.hset(f"package:{id}", "size", package["size"])
    db.hset(f"package:{id}", "status", "label")
    db.sadd(f"user_packages:{username}", f"package:{id}")

    log("Created package: " + str(db.hgetall(f"package:{id}")) + " from sender " + username)

    links = []
    links.append(Link("package:delete", "/sender/" + g.username + "/packages/" + str(id)))

    document = Document(data={"status": "ok"}, links=links)
    return document.to_json()

@app.route("/sender/<username>/packages/<id>", methods=["DELETE"])
def delete_sender_package(username, id):
    if username != g.get("username"):
        return error("Unauthorized", "Brak dostępu.")

    is_package_sender = db.sismember(f"user_packages:{username}", f"package:{id}")

    if not db.hget(f"package:{id}", "recipient"):
        return error("Package not found", "Nie znaleziono paczki")

    if not is_package_sender:
        return error("Unauthorized", "Brak dostępu.", 401)

    if not db.hget(f"package:{id}", "status") == "label":
        return error("Package in transit cannot be deleted", "Nie można usunąć, paczka jest już w drodze.")

    db.srem(f"user_packages:{username}", f"package:{id}")
    db.delete(f"package:{id}")

    log("Deleted package: " + id + " from sender: " + username)

    links = []
    links.append(Link("package:create", "/sender/" + g.username + "/packages"))

    document = Document(data={"status": "ok"}, links=links)
    return document.to_json()


def error(error, error_pl, code=400):
    return {"error": error, "error_pl": error_pl}, code

def log(message):
    time = "INFO [" + str(datetime.now()) + "]"
    print(time + ": " + message, flush=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
