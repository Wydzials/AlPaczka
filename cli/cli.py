from dotenv import load_dotenv
from os import getenv
import requests
from datetime import datetime
from jwt import decode

from PyInquirer import prompt
import os


statuses = {
    "label": "Etykieta",
    "in transit": "W drodze",
    "delivered": "Dostarczona",
    "collected": "Odebrana"
}

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def header():
    clear()
    print("-" * 50)
    print("{:^50}".format("AlPaczka: Aplikacja dla kuriera"))
    print("{:^50}".format("Data ważności tokenu: " + str(exp)))
    print("-" * 50)
    if datetime.utcnow() >= exp:
        print("Twój token jest nieważny!")
        print("Korzystanie z aplikacji wymaga posiadania ważnego tokenu.")
        exit()

def info(message, message2="Naciśnij enter, aby kontynuować..."):
    header()
    print(message + "\n")
    input(message2)

def api(method, url, json=""):
    headers = {"Authorization": TOKEN}
    url = API_URL + url

    try:
        if method == "GET":
            return requests.get(url, json=json, headers=headers)
        elif method == "POST":
            return requests.post(url, json=json, headers=headers)
        elif method == "DELETE":
            return requests.delete(url, json=json, headers=headers)
        elif method == "PATCH":
            return requests.patch(url, json=json, headers=headers)
    except:
        print("Błąd połącznia z API.")
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

    return packages

def labels_list():
    packages_data = get_packages()
    packages = [
        "{: <10} {: <10} {: <10} {: <10}".format("Nadawca", "Odbiorca", "Skrytka", "Rozmiar")
    ]
    for p in packages_data:
        if p.get("status") == "Etykieta":
            package = "{: <10} {: <10} {: <10} {: <10}".format(
                p.get("sender"), 
                p.get("recipient"), 
                p.get("box_id"), 
                p.get("size"), 
            )
            packages.append(package)
    
    questions = {
        "type": "list",
        "name": "package",
        "message": "Wybierz etykietę do utworzenia paczki:\n",
    }
    questions["choices"] = packages

    header()
    answer = prompt(questions)
    while answer.get("package") == packages[0]:
        header()
        answer = prompt(questions)

def change_status(package_id):
    choices = []
    for en, pl in statuses.items():
        choices.append(
            {
                "name": pl,
                "value": en 
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
    r = api("PATCH", f"/courier/packages/{package_id}", {"status": choice})

    if r.status_code == 200:
        info("Zmieniono status paczki na: " + statuses[choice] + ".")
    else:
        json = r.json()
        if json and json.get("error_pl"):
            info("Błąd: " + json.get("error_pl"))


def packages_list():
    packages_data = get_packages()
    row_format = "{: <12} {: <12} {: <10} {: <8} {: <10} {: <20}"

    choices = [
        row_format.format("Nadawca", "Odbiorca", "Skrytka", "Rozmiar", "Status", "ID")
    ]
    for p in packages_data:
        if p.get("status") != "Etykieta":
            name = row_format.format(
                p.get("sender"), 
                p.get("recipient"), 
                p.get("box_id"), 
                p.get("size"), 
                p.get("status"),
                p.get("id")
            )
            choices.append(
                {
                    "name": name,
                    "value": p.get("id")
                }
            )
    choices.append("[ Anuluj ]")

    question = {
        "type": "list",
        "name": "package",
        "message": "Wybierz paczkę do zmiany statusu:\n",
        "choices": choices
    }

    header()
    choice = prompt(question).get("package")
    while choice == choices[0]:
        header()
        choice = prompt(question).get("package")

    if choice != "[ Anuluj ]":
        change_status(choice)

def menu():
    header()
    questions = [
        {
            'type': 'list',
            'name': 'choice',
            'message': 'Wybierz akcję:\n',
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
        labels_list()
    if choice == 1:
        packages_list()
    elif choice == 3:
        clear()
        print("Do zobaczenia!")
        exit()


load_dotenv()
API_URL = getenv("API_URL")
TOKEN = getenv("COURIER_TOKEN")

authorization = decode(TOKEN, verify=False)
exp = datetime.utcfromtimestamp(authorization.get("exp"))

while True:
    menu()
    