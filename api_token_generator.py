from jwt import encode
from datetime import datetime, timedelta
from os import getenv
from dotenv import load_dotenv


load_dotenv()
API_SECRET = str(getenv("API_SECRET"))
JWT_LIFETIME_DAYS = 3

payload = {
    "exp": datetime.utcnow() + timedelta(days=JWT_LIFETIME_DAYS),
    "iat": datetime.utcnow(),
    "sub": "COURIER"
}
token = encode(payload, API_SECRET, algorithm="HS256")
print("TOKEN='" + token.decode() + "'")