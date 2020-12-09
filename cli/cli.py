from dotenv import load_dotenv
from os import getenv
import requests
from datetime import datetime
from jwt import decode

from PyInquirer import prompt
import os


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def header():
    clear()
    print("=== AlPaczka: Aplikacja dla kuriera ===")
    print("Data ważności tokenu: " + str(exp))
    if datetime.utcnow() >= exp:
        print("Twój token jest nieważny!")
        print("Korzystanie z aplikacji wymaga posiadania ważnego tokenu.")
        exit()

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
    except:
        print("Błąd połącznia z API.")
        exit()

def get_packages():
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
    
def packages_list():
    packages_data = get_packages()

    packages = [
        "{: <12} {: <12} {: <10} {: <8} {: <10}".format("Nadawca", "Odbiorca", "Skrytka", "Rozmiar", "Status")
    ]
    for p in packages_data:
        if p.get("status") != "Etykieta":
            package = "{: <12} {: <12} {: <10} {: <8} {: <10}".format(
                p.get("sender"), 
                p.get("recipient"), 
                p.get("box_id"), 
                p.get("size"), 
                p.get("status")
            )
            packages.append(package)
        
    questions = {
        "type": "list",
        "name": "package",
        "message": "Wybierz paczkę do zmiany statusu:\n",
    }
    questions["choices"] = packages

    header()
    answer = prompt(questions)
    while answer.get("package") == packages[0]:
        header()
        answer = prompt(questions)

def menu():
    header()
    questions = [
        {
            'type': 'list',
            'name': 'choice',
            'message': 'Wybierz akcję:',
            "choices": [
                "Lista etykiet: utwórz przesyłkę",
                "Lista przesyłek: zmień status",
                "Informacje",
                "Wyjście"
            ]
        }
    ]
    answers = prompt(questions)
    choice = answers.get("choice")
    if choice == "Lista etykiet: utwórz przesyłkę":
        labels_list()
    if choice == "Lista przesyłek: zmień status":
        packages_list()
    elif choice == "Wyjście":
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
    