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
    if choice == "Wyjście":
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
    

