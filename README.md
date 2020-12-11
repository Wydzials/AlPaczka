# AlPaczka (AlPackage)

## General info
Flask web application for modern package delivery system.

## P3 setup (in development)
### A) Heroku (recommended)
This application is deployed on Heroku: https://alpaczka-dev.herokuapp.com/.

To start the command line app for couriers and connect with API on Heroku, run:
```bash
python3 api_token_generator.py > cli/.env # generate new jwt token
docker build cli/ -t alpaczka-cli
docker run --network="host" -it alpaczka-cli
```

### B) Docker-compose
Before you run this project locally, you need to create `.env` file with enviroment variables for `api` and `web` containers.
In the project folder execute commands:
```bash
echo "WEB_SECRET='[your secret]'" > .env
echo "API_SECRET='[your secret]'" >> .env
```

Then run application with `docker-compose`:
```bash
docker-compose build
docker-compose up
```
Now you should be able to access web application with url `http://localhost:8000/`.


Command line app for couriers also requires `.env` file with token and API url. Create one using:
```bash
python3 api_token_generator.py > cli/.env
echo "API_URL='http://0.0.0.0:8001'" >> cli/.env
```
Then run the app:
```bash
docker build cli/ -t alpaczka-cli
docker run --network="host" -it alpaczka-cli
```

## Older releases
### P2
First you need to create `.env` file with secret key for Flask:
```bash
echo "SECRET_KEY='[paste your key here]'" > .env
```

Then run application with `docker-compose`:
```bash
docker-compose build
docker-compose up
```
Release P2 is also deployed on Heroku: https://alpaczka.herokuapp.com/.
