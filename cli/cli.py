from dotenv import load_dotenv
from os import getenv, name, system
from datetime import datetime
from jwt import decode
from PyInquirer import prompt
import requests
import sys


WIDTH = 60
row = "{:^" + str(WIDTH) + "}"
statuses = {
    "label": "Etykieta",
    "in transit": "W drodze",
    "delivered": "Dostarczona",
    "collected": "Odebrana"
}
flash_messages = ["Sterowanie: strzałki + enter"]


def clear():
    system("cls" if name == "nt" else "clear")


def header():
    clear()
    print("-" * WIDTH)
    print(row.format("AlPaczka: Aplikacja dla kuriera"))

    delta = exp - datetime.utcnow()
    prefix = "Twój token jest ważny jeszcze przez"
    if delta.days == 1:
        print(row.format(f"{prefix} 1 dzień."))
    elif delta.days > 1:
        print(row.format(f"{prefix} {delta.days} dni."))
    else:
        print(row.format(f"{prefix} {delta.seconds // 3600} godzin."))

    print("-" * WIDTH)
    if datetime.utcnow() >= exp:
        print("Twój token jest nieważny!")
        print("Aby skorzystać z aplikacji, musisz wygenerować nowy token.")
        exit()

    for message in flash_messages:
        print(row.format("(!) " + message))
    flash_messages.clear()


def api(method, url, json=""):
    headers = {"authorization": "Bearer " + TOKEN}
    url = API_URL + url

    try:
        if method == "GET":
            r = requests.get(url, json=json, headers=headers)
        elif method == "POST":
            r = requests.post(url, json=json, headers=headers)
        elif method == "DELETE":
            r = requests.delete(url, json=json, headers=headers)
        elif method == "PATCH":
            r = requests.patch(url, json=json, headers=headers)

        if r.status_code != 200:
            print("Błąd połączenia z API")
            error = r.json().get("error_pl")
            if error:
                print(error)
            exit()
        return r
    except:
        print("Błąd połączenia z API.")
        exit()


def get_packages():
    sizes = {
        1: "Mały",
        2: "Średni",
        3: "Duży"
    }

    r = api("GET", "/courier/packages")
    data = r.json()

    packages = data.get("packages")
    for package in packages:
        package["size"] = sizes[int(package["size"])]
        package["status"] = statuses[package["status"]]
        if "auth0-" in package["sender"]:
            package["sender"] = package["sender"][6:]

    return packages


def label_to_package(package_id):
    header()
    question = {
        "type": "list",
        "name": "label",
        "message": "Czy na pewno chcesz utworzyć paczkę?\n",
        "choices": [
            {
                "name": "Tak",
                "value": 1
            },
            {
                "name": "Nie",
                "value": 0
            }
        ],
        "default": 1
    }

    choice = prompt(question).get("label")
    if choice:
        r = api(
            "PATCH", f"/courier/packages/{package_id}", {"status": "in transit"})

        if r.status_code == 200:
            flash_messages.append("Utworzono paczkę z wybranej etykiety.")
        else:
            json = r.json()
            if json and json.get("error_pl"):
                flash_messages.append("Błąd: " + json.get("error_pl"))


def list_menu(message, labels):
    packages_data = get_packages()
    row_format = "{: <10} {: <8} {: <12} {: <14} {: <14}"

    choices = [
        row_format.format("Skrytka", "Rozmiar", "Status",
                          "Nadawca", "Odbiorca")
    ]
    for p in packages_data:
        if (p.get("status") == "Etykieta") == labels:
            name = row_format.format(
                p.get("box_id"),
                p.get("size"),
                p.get("status"),
                p.get("sender"),
                p.get("recipient")
            )
            choices.append(
                {
                    "name": name,
                    "value": p.get("id")
                }
            )
    if len(choices) == 1:
        flash_messages.append("Brak paczek do edycji!")
        flash_messages.append("Poczekajmy, aż klienci coś wyślą.")
        return "cancel"

    choices.append(
        {
            "name": "[ Anuluj ]",
            "value": "cancel"
        }
    )

    question = {
        "type": "list",
        "name": "value",
        "message": message + "\n",
        "choices": choices,
        "default": len(choices) - 1
    }

    header()
    choice = prompt(question).get("value")
    while choice is None or choice == choices[0]:
        header()
        choice = prompt(question).get("value")

    return choice


def change_status(package_id):
    choices = []
    for en, pl in statuses.items():
        choices.append(
            {
                "name": pl,
                "value": en
            }
        )
    choices.append(
        {
            "name": "[ Anuluj ]",
            "value": "cancel"
        }
    )

    question = {
        "type": "list",
        "name": "package",
        "message": "Wybierz nowy status dla paczki:\n",
        "choices": choices
    }

    header()
    choice = prompt(question).get("package")
    if choice == "cancel":
        return

    r = api("PATCH", f"/courier/packages/{package_id}", {"status": choice})

    if r.status_code == 200:
        flash_messages.append(
            "Zmieniono status paczki na: " + statuses[choice] + ".")
    else:
        json = r.json()
        if json and json.get("error_pl"):
            flash_messages.append("Błąd: " + json.get("error_pl"))


def menu():
    header()
    questions = [
        {
            "type": "list",
            "name": "choice",
            "message": "Wybierz akcję:\n",
            "choices": [
                {
                    "name": "Lista etykiet: utwórz paczkę",
                    "value": 0
                },
                {
                    "name": "Lista paczek: zmień status",
                    "value": 1
                },
                {
                    "name": "Informacje",
                    "value": 2
                },
                {
                    "name": "Wyjście",
                    "value": 3
                }
            ]
        }
    ]
    answers = prompt(questions)
    choice = answers.get("choice")

    if choice == 0:
        choice = list_menu(
            "Wybierz etykietę do utworzenia paczki:", labels=True)
        if choice != "cancel":
            label_to_package(choice)

    elif choice == 1:
        choice = list_menu("Wybierz paczkę do zmiany statusu:", labels=False)
        if choice != "cancel":
            change_status(choice)

    elif choice == 2:
        header()
        print(" Witaj w aplikacji dla kuriera AlPaczka!")
        print(" Sterowanie odbywa się przy użyciu klawiszy \n strzałek (góra/dół) oraz entera.")
        print(" API: " + API_URL)
        print(" Miłego paczkowania!\n")
        input(" [Enter] Powrót do menu")

    elif choice == 3:
        clear()
        print("Do zobaczenia!")
        exit()


def login():
    questions = [
        {
            "type": "input",
            "name": "username",
            "message": "Nazwa użytkownika: ",
        },
        {
            "type": "password",
            "name": "password",
            "message": "Hasło: ",
        }
    ]
    clear()
    answers = prompt(questions)
    return answers.get("username"), answers.get("password")


def get_token(username, password):
    headers = {"content-type": "application/x-www-form-urlencoded"}
    data = {
        "username": username,
        "password": password,
        "grant_type": "password",
        "audience": API_IDENTIFIER,
        "scope": "openid",
        "client_id": "kAutGBEknui7WbLTY3f1MuvkAALUSvIJ",
        "client_secret": "RTi6Lc782ibva5Ty3W1wPtfOsmYPNg94-3CFGpQrceRkhIygaIXknl9RWHUjSWSO"
    }
    r = requests.post(AUTH0_DOMAIN + "/oauth/token",
                      data=data, headers=headers)

    return r.json().get("access_token")


if len(sys.argv) < 2:
    API_URL = "https://alpaczka-api.herokuapp.com"
else:
    API_URL = sys.argv[1]

load_dotenv()
AUTH0_DOMAIN = "https://" + getenv("AUTH0_CLI_DOMAIN", "")
API_IDENTIFIER = getenv("API_IDENTIFIER")

username, password = login()
TOKEN = get_token(username, password)

try:
    authorization = decode(TOKEN, algorithms=["HS256"], options={
        "verify_signature": False}, audience=API_IDENTIFIER)
    exp = datetime.utcfromtimestamp(authorization.get("exp"))
except:
    print("Nieprawidłowe dane logowania.")
    exit()


while True:
    menu()
