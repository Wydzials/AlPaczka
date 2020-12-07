from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from flask_session import Session

from redis import Redis
from dotenv import load_dotenv
from bcrypt import hashpw, gensalt, checkpw
from datetime import datetime
from uuid import uuid4
import re, os, requests
from jwt import decode


app = Flask(__name__)
load_dotenv()

cloud_url = os.environ.get("REDIS_URL")
db = Redis.from_url(cloud_url) if cloud_url else Redis(host="redis")

if cloud_url:
    SESSION_COOKIE_SECURE = True

SESSION_TYPE = "filesystem"
PERMANENT_SESSION_LIFETIME = 600
SESSION_COOKIE_HTTPONLY = True
SECRET_KEY = os.getenv("SECRET_KEY")

app.config.from_object(__name__)
ses = Session(app)
API_URL = os.getenv("API_URL")


@app.errorhandler(500)
def internal_error(error):
    message = "Nieznany błąd serwera."
    try:
        db.ping()
    except:
        message = "Błąd połączenia z bazą danych."
        
    return render_template("error.html", error_message=message)

@app.before_request
def before_request():
    g.username = session.get("username")

    token = session.get("token")
    if token:
        authorization = decode(token, verify=False)
        exp = datetime.utcfromtimestamp(authorization.get("exp"))

        print(exp, flush=True)
        if datetime.utcnow() > exp:
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

    field_names = ["username", "firstname", "lastname", "email", "address", "password", "password2"]
    errors = {"username": "nazwy użytkownika",
              "firstname": "imienia",
              "lastname": "nazwiska",
              "email": "adresu email",
              "address": "adresu",
              "password": "hasła",
              "password2": "potwierdzenia hasła"}
    fields = {}
    correct = True
    session.pop('_flashes', None)

    for name in field_names:
        fields[name] = request.form.get(name)
        if not fields[name]:
            flash(f"Nie podano {errors[name]}.", "danger")
            correct = False

    if fields["password"] != fields["password2"]:
        flash("Hasła nie są takie same.", "danger")
        correct = False
    
    if fields["username"] and not re.fullmatch(r'^[a-z]{3,20}', fields["username"]):
        flash("Nazwa użytkownika musi składać się z 3-20 małych liter.", "danger")
        correct = False
    
    if fields["username"] and db.hexists(f"user:{fields['username']}", "password"):
        flash("Nazwa użytkownika jest zajęta.", "danger")
        correct = False

    if not correct:
        return redirect(url_for("sender_register"))

    db.hset(f"user:{fields['username']}", "firstname", fields["firstname"])
    db.hset(f"user:{fields['username']}", "lastname", fields["lastname"])
    db.hset(f"user:{fields['username']}", "address", fields["address"])
    db.hset(f"user:{fields['username']}", "email", fields["email"])

    password = fields["password"].encode()
    hashed = hashpw(password, gensalt(5))
    db.hset(f"user:{fields['username']}", "password", hashed)

    flash("Pomyślnie zarejestrowano konto nadawcy.", "success")
    return redirect(url_for("index"))


@app.route("/sender/login", methods=["GET", "POST"])
def sender_login():
    if request.method == "GET":
        return render_template("sender_login.html")
    
    session.pop('_flashes', None)

    username = request.form.get("username")
    password = request.form.get("password")

    r = requests.get(API_URL + "/login", json={"username": username, "password": password})
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
    session.clear()
    flash("Wylogowano pomyślnie.", "success")
    return redirect(url_for("index"))


@app.route("/sender/dashboard", methods=["GET", "POST"])
def sender_dashboard():
    if not g.username:
        return redirect(url_for("index"))

    if request.method == "GET":
        package_sizes = {1: "Mały", 2: "Średni", 3: "Duży"}

        headers = {"Authorization": session.get("token")}
        url = API_URL + "/sender/" + g.username + "/packages"
        r = requests.get(url, headers=headers)
        packages = r.json().get("packages")

        return render_template("sender_dashboard.html", packages=packages, sizes=package_sizes)
    
    session.pop('_flashes', None)
    package = {"recipient": request.form.get("recipient"),
            "box_id": request.form.get("box-id"),
            "size": request.form.get("size")}
    
    headers = {"Authorization": session.get("token")}
    url = API_URL + "/sender/" + g.username + "/packages"
    r = requests.post(url, json=package, headers=headers)

    error_pl = r.json().get("error_pl")
    if error_pl:
        flash(error_pl, "danger")
        return redirect(url_for("sender_dashboard"))

    return redirect(url_for("sender_dashboard"))


def is_package_sender(sender, package_id):
    return db.sismember(f"user_packages:{sender}", f"package:{package_id}")


@app.route("/package/delete/<id>")
def delete_package(id):
    if not g.username:
        return redirect(url_for("sender_dashboard"))

    headers = {"Authorization": session.get("token")}
    url = API_URL + "/sender/" + g.username + "/packages/" + id
    r = requests.delete(url, headers=headers)
    
    error_pl = r.json().get("error_pl")
    if error_pl:
        flash(error_pl, "danger")

    return redirect(url_for("sender_dashboard"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
