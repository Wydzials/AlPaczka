# AlPaczka (AlPackage)

## General info
Flask web application for modern package delivery system.

## P3 setup
### A) Heroku (recommended)
This application is deployed on Heroku: https://alpaczka-p3.herokuapp.com/.

You can run the command line app for couriers and connect with API on Heroku using bash script:
```bash
./run-cli.sh heroku
```

### B) Docker-compose
#### Easy way
When running the application for the first time, you have to provide secrets for `api` and `web`. Next time just run the script with no arguments.
```bash
./run-docker-compose.sh [web secret] [api secret]
```

Then start command line app for couriers:
```
./run-cli.sh local
```

#### Hard way
If you don't want to use the scripts, first you need to create `.env` file with enviroment variables for `api` and `web` containers.
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
Now you should be able to access web application with url http://localhost:8000/.


Command line app for couriers also requires `.env` file with token and API url. Create one using:
```bash
echo "TOKEN='`python3 api_token_generator.py`'" > cli/.env
echo "API_URL='http://0.0.0.0:8001'" >> cli/.env
```
Then run the app:
```bash
docker build cli/ -t alpaczka-cli
docker run --network="host" -it alpaczka-cli
```

## Older releases
### P2 Setup
Create `.env` file with secret key for Flask:
```bash
echo "SECRET_KEY='[paste your key here]'" > .env
```

Then run the application with `docker-compose`:
```bash
docker-compose build
docker-compose up
```
Release P2 is also deployed on Heroku: https://alpaczka.herokuapp.com/.
