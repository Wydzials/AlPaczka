from flask import Flask, render_template, request, redirect, url_for, flash
from flask_session import Session

from redis import Redis
from os import getenv
from dotenv import load_dotenv
from bcrypt import hashpw, gensalt, checkpw


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

@app.route("/sender/register", methods=["GET", "POST"])
def sender_register():
    if request.method == "GET":
        return render_template("sender_register.html")

    field_names = ["username", "firstname", "lastname", "email", "address", "password", "password2"]
    empty_errors = {"username": "nazwy użytkownika",
                    "firstname": "imienia",
                    "lastname": "nazwiska",
                    "email": "adresu email",
                    "address": "adresu",
                    "password": "hasła",
                    "password2": "potwierdzenia hasła"}

    fields = {}
    correct = True

    for name in field_names:
        fields[name] = request.form.get(name)
        if not fields[name]:
            flash(f"Nie podano {empty_errors[name]}!")
            correct = False

    if fields["password"] != fields["password2"]:
        flash("Hasła nie są takie same!")
        correct = False
    
    if fields["username"] and db.hexists(f"user:{fields['username']}", "password"):
        flash("Nazwa użytkownika jest zajęta!")
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

    flash(f"Pomyślnie zarejestrowano nadawcę {fields['username']}.")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
