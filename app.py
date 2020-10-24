from flask import Flask, render_template
app = Flask(__name__)
app.debug = True


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/sender/sign-up")
def sender_sign_up():
    return render_template("sender_sign_up.html")

app.run(host="0.0.0.0", port=5000)