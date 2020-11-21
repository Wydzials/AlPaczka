from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from flask_session import Session

from redis import Redis, StrictRedis
from dotenv import load_dotenv
from bcrypt import hashpw, gensalt, checkpw
from datetime import datetime
from uuid import uuid4
import re, os


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
    
    username = request.form.get("username")
    password = request.form.get("password")

    session.pop('_flashes', None)

    if not username:
        flash("Nazwa użytkownika nie może być pusta.", "danger")
        return redirect(url_for("sender_login"))

    if not password:
        flash("Hasło nie może być puste.", "danger")
        return redirect(url_for("sender_login"))

    db_password = db.hget(f"user:{username}", "password")

    if not db_password:
        flash("Nie znaleziono użytkownika o podanej nazwie.", "danger")
        return redirect(url_for("sender_login"))
    
    if not checkpw(password.encode(), db_password):
        flash("Nieprawidłowe hasło.", "danger")
        return redirect(url_for("sender_login"))
    
    session["username"] = username
    session["logged-at"] = datetime.now()
    flash("Zalogowano na konto nadawcy.", "success")
    return redirect(url_for("sender_dashboard"))

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

        package_names = db.smembers(f"user_packages:{g.username}")

        packages = []
        for name in package_names:
            byte_package = db.hgetall(name).items()
            package = {key.decode(): value.decode() for key, value in byte_package}
            package["size"] = package_sizes[int(package["size"])]
            package["id"] = name.decode().replace("package:", "")
            packages.append(package)

        packages = sorted(packages, key=lambda k: int(k["box_id"]))

        return render_template("sender_dashboard.html", packages=packages, sizes=package_sizes)
    
    recipient = request.form.get("recipient")
    box_id = request.form.get("box-id")
    size = request.form.get("size")

    session.pop('_flashes', None)

    if not recipient:
        flash("Nazwa adresata nie może być pusta.", "danger")
        return redirect(url_for("sender_dashboard"))
    
    if not box_id:
        flash("Identyfikator skrytki nie może być pusty.", "danger")
        return redirect(url_for("sender_dashboard"))

    if not size:
        flash("Rozmiar nie może być pusty.", "danger")
        return redirect(url_for("sender_dashboard"))
    
    id = uuid4()
    db.hset(f"package:{id}", "recipient", recipient)
    db.hset(f"package:{id}", "box_id", box_id)
    db.hset(f"package:{id}", "size", size)

    db.sadd(f"user_packages:{g.username}", f"package:{id}")

    return redirect(url_for("sender_dashboard"))

def is_package_sender(sender, package_id):
    return db.sismember(f"user_packages:{sender}", f"package:{package_id}")

@app.route("/package/delete/<id>")
def delete_package(id):
    if is_package_sender(g.username, id):
        db.srem(f"user_packages:{g.username}", f"package:{id}")
        db.delete(f"package:{id}")
        return redirect(url_for("sender_dashboard"))
    else:
        return "Brak dostępu", 401


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False)
