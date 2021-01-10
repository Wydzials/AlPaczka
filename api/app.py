from flask import Flask, request, g, make_response
from flask_hal import HAL
from flask_hal.document import Document, Embedded
from flask_hal.link import Link

from redis import Redis
from dotenv import load_dotenv
from bcrypt import hashpw, gensalt, checkpw
from datetime import datetime, timedelta
from jwt import encode, decode, ExpiredSignatureError
from uuid import uuid4
from os import getenv
from functools import wraps
from six.moves.urllib.request import urlopen
from jose import jwt

import json
import re
import time


app = Flask(__name__)
HAL(app)
load_dotenv()

cloud_url = getenv("REDIS_URL")
db = Redis.from_url(cloud_url, decode_responses=True) if cloud_url else Redis(
    host="redis", decode_responses=True)

JWT_SECRET = getenv("API_SECRET")
app.config.from_object(__name__)

JWT_LIFETIME = 300
COURIER_NAME = "COURIER"

AUTH0_CLI_DOMAIN = getenv("AUTH0_CLI_DOMAIN")
API_IDENTIFIER = getenv("API_IDENTIFIER")


class AuthError(Exception):
    def __init__(self, error=None, status_code=401):
        self.error = error
        self.status_code = status_code


@app.errorhandler(AuthError)
def handle_auth_error(e):
    log(str(e))
    data = {"error": "Invalid token",
            "error_pl": "Błędny token."}
    document = Document(data=data)
    return document.to_json(), 401


def sender_token_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        try:
            authorization = decode(token, JWT_SECRET, algorithms=["HS256"])
            g.username = authorization.get("sub")
        except ExpiredSignatureError:
            if request.path != "/login":
                log("Expired token for path: " + request.path)

                links = [Link("login", "/login")]
                data = {"error": "Expired token",
                        "error_pl": "Token wygasł, zaloguj się ponownie."}
                document = Document(data=data, links=links)
                return document.to_json(), 401
        except Exception as e:
            log("Unauthorized: " + str(e))
            g.username = ""
        return function(*args, **kwargs)
    return wrapper


def courier_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", None)
        if not auth:
            raise AuthError()

        parts = auth.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise AuthError()
        token = parts[1]

        jsonurl = urlopen("https://"+AUTH0_CLI_DOMAIN+"/.well-known/jwks.json")
        jwks = json.loads(jsonurl.read())

        try:
            unverified_header = jwt.get_unverified_header(token)
        except Exception:
            raise AuthError()

        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
        if rsa_key:
            try:
                jwt.decode(
                    token,
                    rsa_key,
                    algorithms=["RS256"],
                    audience=API_IDENTIFIER,
                    issuer="https://"+AUTH0_CLI_DOMAIN+"/"
                )
            except Exception:
                raise AuthError()

            g.username = "COURIER"
            return f(*args, **kwargs)
        raise AuthError()
    return decorated


@app.route("/sender/register", methods=["POST"])
def register():
    data = request.json

    if not data:
        return {"error": "No JSON provided"}, 400

    names_and_errors = {
        "username": "nazwy użytkownika",
        "firstname": "imienia",
        "lastname": "nazwiska",
        "email": "adresu email",
        "address": "adresu",
        "password": "hasła",
        "password2": "potwierdzenia hasła"
    }

    errors = []
    errors_pl = []
    fields = {}

    for name in names_and_errors:
        fields[name] = data.get(name)
        if not fields[name]:
            errors.append("No " + name + " provided.")
            errors_pl.append(f"Nie podano {names_and_errors[name]}.")

    if fields["password"] != fields["password2"]:
        errors.append("Passwords does not match")
        errors_pl.append("Hasła nie są takie same.")

    if fields["username"] and not re.fullmatch(r"^[a-z]{3,20}", fields["username"]):
        errors.append("Username must contain only 3-20 lowercase letters")
        errors_pl.append(
            "Nazwa użytkownika musi składać się z 3-20 małych liter.")

    if fields["username"] and db.hexists(f"user:{fields['username']}", "password"):
        errors.append("Username is taken")
        errors_pl.append("Nazwa użytkownika jest zajęta.")

    if len(errors) > 0:
        return error(errors, errors_pl)

    db.hset(f"user:{fields['username']}", "firstname", fields["firstname"])
    db.hset(f"user:{fields['username']}", "lastname", fields["lastname"])
    db.hset(f"user:{fields['username']}", "address", fields["address"])
    db.hset(f"user:{fields['username']}", "email", fields["email"])

    password = fields["password"].encode()
    hashed = hashpw(password, gensalt(5))
    db.hset(f"user:{fields['username']}", "password", hashed)
    db.sadd("users", fields["username"])

    links = [Link("sender:login", "/sender/login")]

    document = Document(links=links)
    return document.to_json(), 201


@app.route("/sender/login", methods=["GET"])
def login():
    json = request.json

    if not json:
        return {"error": "No JSON provided"}, 400

    username = json.get("username")
    password = json.get("password")
    db_password = db.hget(f"user:{username}", "password")

    if not username:
        return error("No username provided", "Nazwa użytkownika nie może być pusta.")

    if not password:
        return error("No password provided", "Hasło nie może być puste.")

    if not db_password:
        return error("Invalid username", "Nieprawidłowa nazwa użytkownika.")

    if not checkpw(password.encode(), db_password.encode()):
        return error("Invalid password", "Nieprawidłowe hasło.")

    log("Logged in user " + username)

    payload = {
        "exp": datetime.utcnow() + timedelta(seconds=JWT_LIFETIME),
        "iat": datetime.utcnow(),
        "sub": username
    }
    token = encode(payload, str(JWT_SECRET), algorithm="HS256")

    links = [
        Link("sender:dashboard", "/sender/dashboard"),
        Link("sender:logout", "/sender/logout")
    ]

    document = Document(data={"status": "logged-in",
                              "token": token}, links=links)
    return document.to_json()


@app.route("/sender/<username>/packages", methods=["GET"])
@sender_token_required
def get_sender_packages(username):
    if username != g.get("username") or g.get("username") == COURIER_NAME:
        return error("Unauthorized", "Brak dostępu.")

    package_names = db.smembers(f"user_packages:{username}")
    packages = []
    for name in package_names:
        package = db.hgetall(name)
        package["id"] = name.replace("package:", "")
        packages.append(package)

    packages = sorted(packages, key=lambda k: int(k["box_id"]))

    links = [
        Link("package:create", "/sender/" + g.username + "/packages"),
        Link("package:delete", "/sender/" + g.username +
             "/packages/{id}", templated=True)
    ]

    document = Document(data={"packages": packages}, links=links)
    return document.to_json()


@app.route("/sender/<username>/packages", methods=["POST"])
@sender_token_required
def add_sender_package(username):
    if username != g.get("username") or g.get("username") == COURIER_NAME:
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

    size = int(package.get("size"))
    if size not in [1, 2, 3]:
        return error("Invalid size", "Nieprawidłowy rozmiar paczki.")

    id = uuid4()
    db.hset(f"package:{id}", "recipient", package["recipient"])
    db.hset(f"package:{id}", "sender", username)
    db.hset(f"package:{id}", "box_id", box_id)
    db.hset(f"package:{id}", "size", size)
    db.hset(f"package:{id}", "status", "label")
    db.sadd(f"user_packages:{username}", f"package:{id}")

    log("Created package: " +
        str(db.hgetall(f"package:{id}")) + " from sender " + username)

    links = [Link("package:delete", "/sender/" +
                  g.username + "/packages/" + str(id))]
    document = Document(links=links)
    return document.to_json(), 201


@app.route("/sender/<username>/packages/<id>", methods=["DELETE"])
@sender_token_required
def delete_sender_package(username, id):
    if username != g.get("username") or g.get("username") == COURIER_NAME:
        return error("Unauthorized", "Brak dostępu.", 401)

    is_package_sender = db.sismember(
        f"user_packages:{username}", f"package:{id}")

    if not db.hget(f"package:{id}", "recipient"):
        return error("Package not found", "Nie znaleziono paczki")

    if not is_package_sender:
        return error("Unauthorized", "Brak dostępu.", 401)

    if not db.hget(f"package:{id}", "status") == "label":
        return error("Package in transit cannot be deleted", "Nie można usunąć, paczka jest już w drodze.")

    db.srem(f"user_packages:{username}", f"package:{id}")
    db.delete(f"package:{id}")

    log("Deleted package: " + id + " from sender: " + username)

    links = [Link("package:create", "/sender/" + g.username + "/packages")]
    document = Document(data={"status": "ok"}, links=links)
    return document.to_json()


def error(error, error_pl, code=400):
    return {"error": error, "error_pl": error_pl}, code


def log(message):
    time = "INFO [" + str(datetime.now()) + "]"
    print(time + ": " + message, flush=True)


@app.route("/courier/packages")
@courier_token_required
def courier_packages():
    if g.username != COURIER_NAME:
        return error("Unauthorized", "Brak dostępu.", 401)

    packages = []
    for user in db.smembers("users"):
        for package_name in db.smembers(f"user_packages:{user}"):
            package = db.hgetall(package_name)
            package["id"] = package_name.replace("package:", "")
            package["sender"] = user
            packages.append(package)

    links = [Link("package:update_status",
                  "/courier/packages/{id}", templated=True)]
    document = Document(data={"packages": packages}, links=links)
    return document.to_json()


@app.route("/courier/packages/<id>", methods=["PATCH"])
@courier_token_required
def change_status(id):
    if g.username != COURIER_NAME:
        return error("Unauthorized", "Brak dostępu.", 401)

    json_data = request.json
    if not json_data:
        return error("No JSON provided", "Niepoprawne żądanie, brak zawartości JSON.")

    status = json_data.get("status")
    if status not in ["label", "in transit", "delivered", "collected"]:
        return error("Invalid status type", "Nieprawidłowy status paczki.")

    package = "package:" + id
    if not db.hexists(package, "status"):
        return error("Package not found", "Nie znaleziono paczki o danym identyfikatorze.")

    if status != db.hget(package, "status"):
        sender = db.hget(package, "sender")
        recipient = db.hget(package, "recipient")
        box_id = db.hget(package, "box_id")
        db.publish(
            f"user:{sender}", f"Nowy status paczki dla adresata '{recipient}', nadanej do skrytki numer {box_id}!\nOdśwież stronę, aby zobaczyć zmiany.")
        db.hset(package, "status", status)

    links = [Link("packages", "/courier/packages")]
    document = Document(data={"package": db.hgetall(package)}, links=links)
    return document.to_json()


@app.route('/notifications')
@sender_token_required
def poll():
    username = g.get("username")
    sub = db.pubsub()
    sub.subscribe(f"user:{username}")

    for i in range(10):
        message = sub.get_message(ignore_subscribe_messages=True)
        if message:
            return {"data": str(message.get("data"))}
        time.sleep(1)
    
    sub.unsubscribe()
    return "", 204


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
