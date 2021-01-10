from flask import Flask, render_template, request, redirect, url_for, flash, session, g, make_response
from flask_session import Session

from redis import Redis
from dotenv import load_dotenv
from bcrypt import hashpw, gensalt, checkpw
from datetime import datetime
from uuid import uuid4
from os import getenv
from jwt import decode, encode
from werkzeug.exceptions import ServiceUnavailable
from six.moves.urllib.parse import urlencode
from authlib.integrations.flask_client import OAuth
from datetime import timedelta

import re
import requests
import time


app = Flask(__name__)
load_dotenv()

cloud_url = getenv("REDIS_URL")
db = Redis.from_url(cloud_url, decode_responses=True) if cloud_url else Redis(
    host="redis", decode_responses=True)


SESSION_TYPE = "filesystem"
PERMANENT_SESSION_LIFETIME = 600
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True
SECRET_KEY = getenv("WEB_SECRET")

API_URL = getenv("API_URL")
if API_URL is None:
    API_URL = "http://api:8000"

app.config.from_object(__name__)
ses = Session(app)


oauth = OAuth(app)
AUTH0_CALLBACK_URL = getenv("AUTH0_CALLBACK_URL")
AUTH0_CLIENT_ID = getenv("AUTH0_CLIENT_ID")
AUTH0_CLIENT_SECRET = getenv("AUTH0_CLIENT_SECRET")
AUTH0_DOMAIN = getenv("AUTH0_DOMAIN")
AUTH0_BASE_URL = "https://" + getenv("AUTH0_DOMAIN")


auth0 = oauth.register(
    'auth0',
    client_id=AUTH0_CLIENT_ID,
    client_secret=AUTH0_CLIENT_SECRET,
    api_base_url=AUTH0_BASE_URL,
    access_token_url=AUTH0_BASE_URL + '/oauth/token',
    authorize_url=AUTH0_BASE_URL + '/authorize',
    client_kwargs={
        'scope': 'openid profile email',
    },
)


@app.route("/auth0/login")
def auth0_login():
    return auth0.authorize_redirect(redirect_uri=AUTH0_CALLBACK_URL)


@app.route("/auth0/callback")
def auth0_callback():
    try:
        auth0.authorize_access_token()
        resp = auth0.get('userinfo')
        userinfo = resp.json()
        username = "auth0-" + userinfo['nickname']
    except:
        flash("Próba zalogowania nie powiodła się.")
        return redirect(url_for("sender_login"))

    if not db.sismember("users", username):
        db.hset(f"user:{username}", "email", userinfo.get("email"))
        db.sadd("users", username)

    payload = {
        "exp": datetime.utcnow() + timedelta(seconds=300),
        "iat": datetime.utcnow(),
        "sub": username
    }
    session["token"] = encode(payload, getenv("API_SECRET"), algorithm="HS256")
    session["username"] = username
    session["logged-at"] = datetime.now()

    flash("Zalogowano na konto nadawcy.", "success")
    return redirect(url_for("sender_dashboard"))


@app.errorhandler(500)
def internal_error(error):
    print("Error 500: " + str(error), flush=True)
    return render_template("error.html", error_message="Nieznany błąd serwera."), 500


@app.errorhandler(ServiceUnavailable)
def api_connection_error(error):
    print(str(error), flush=True)
    return render_template("error.html", error_message="Błąd połączenia z API."), 503


@app.before_request
def before_request():
    g.username = session.get("username")

    token = session.get("token")
    if token:
        authorization = decode(token, algorithms=["HS256"], options={
                               "verify_signature": False})
        exp = datetime.utcfromtimestamp(authorization.get("exp"))

        if request.path != "/notifications" and datetime.utcnow() > exp:
            session.clear()
            flash("Sesja wygasła, zaloguj się ponownie.", "warning")
            return redirect(url_for("sender_login"))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/sender/register", methods=["GET", "POST"])
def sender_register():
    if request.method == "GET":
        return render_template("sender_register.html")

    fields = [
        "username",
        "firstname",
        "lastname",
        "email",
        "address",
        "password",
        "password2"
    ]

    user = {}
    session.pop("_flashes", None)

    for name in fields:
        user[name] = request.form.get(name)

    r = api("POST", "/sender/register", user, authorize=False)
    json = r.json()

    if json.get("error_pl"):
        for error in json.get("error_pl"):
            flash(error, "danger")
        return redirect(url_for("sender_register"))

    flash("Pomyślnie zarejestrowano konto nadawcy.", "success")
    return redirect(url_for("index"))


@app.route("/sender/login", methods=["GET", "POST"])
def sender_login():
    if request.method == "GET":
        return render_template("sender_login.html")

    session.pop("_flashes", None)

    username = request.form.get("username")
    password = request.form.get("password")

    r = api("GET", "/sender/login",
            {"username": username, "password": password}, authorize=False)
    json = r.json()

    if json.get("status") == "logged-in":
        session["username"] = username
        session["logged-at"] = datetime.now()
        flash("Zalogowano na konto nadawcy.", "success")
        session["token"] = json.get("token")
        return redirect(url_for("sender_dashboard"))

    error_pl = json.get("error_pl")
    if error_pl:
        flash(error_pl, "danger")
        return redirect(url_for("sender_login"))

    flash("Nieznany błąd", "danger")
    return redirect(url_for("sender_login"))


@app.route("/sender/logout")
def sender_logout():
    flash("Wylogowano pomyślnie.", "success")

    if "auth0-" in session.get("username", ""):
        session.clear()
        params = {'returnTo': url_for('index', _external=True),
                  'client_id': AUTH0_CLIENT_ID}
        return redirect(auth0.api_base_url + '/v2/logout?' + urlencode(params))
    else:
        session.clear()
        return redirect(url_for("index"))


@app.route("/sender/dashboard", methods=["GET", "POST"])
def sender_dashboard():
    if not g.username:
        return redirect(url_for("index"))

    if request.method == "GET":
        sizes = {
            1: "Mały",
            2: "Średni",
            3: "Duży"
        }

        statuses = {
            "label": "Etykieta",
            "in transit": "W drodze",
            "delivered": "Dostarczona",
            "collected": "Odebrana"
        }

        url = "/sender/" + g.username + "/packages"
        r = api("GET", url)
        packages = r.json().get("packages")

        for package in packages:
            package["status"] = statuses[package["status"]]
            package["size"] = sizes[int(package["size"])]

        return render_template("sender_dashboard.html", packages=packages, sizes=sizes)

    session.pop("_flashes", None)
    package = {
        "recipient": request.form.get("recipient"),
        "box_id": request.form.get("box-id"),
        "size": request.form.get("size")
    }

    url = "/sender/" + g.username + "/packages"
    r = api("POST", url, json=package)

    error_pl = r.json().get("error_pl")
    if error_pl:
        flash(error_pl, "danger")
        return redirect(url_for("sender_dashboard"))

    return redirect(url_for("sender_dashboard"))


@app.route("/package/delete/<id>")
def delete_package(id):
    if not g.username:
        return redirect(url_for("sender_dashboard"))

    url = "/sender/" + g.username + "/packages/" + id
    r = api("DELETE", url)

    error_pl = r.json().get("error_pl")
    if error_pl:
        flash(error_pl, "danger")

    return redirect(url_for("sender_dashboard"))


def api(method, url, json="", authorize=True):
    headers = {"Authorization": session.get("token")} if authorize else ""
    url = API_URL + url

    try:
        if method == "GET":
            return requests.get(url, json=json, headers=headers)
        elif method == "POST":
            return requests.post(url, json=json, headers=headers)
        elif method == "DELETE":
            return requests.delete(url, json=json, headers=headers)
    except Exception as e:
        raise ServiceUnavailable("API connection error: " + str(e))


@app.route('/notifications')
def poll():
    if not g.get("username"):
        return "Unathorized", 401

    r = api("GET", "/notifications")

    if r.status_code == 200:
        data = r.json().get("data")
        response = make_response(data, 200)
    elif r.status_code == 401:
        response = make_response("", 401)
    else:
        response = make_response("", 204)

    origin = request.headers.get('Origin')
    allowed_origins = ["http://0.0.0.0:8000", "http://0.0.0.0:8000/"]
    if origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"

    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
