# AlPaczka (AlPackage)

## General info
Flask web application for modern package delivery system.

## P4 Setup
### A) Heroku
This application is deployed on Heroku: https://alpaczka-p4.herokuapp.com/.

To run the command line app for couriers, you need to create `cli/.env` file with auth0 api parameters:
```
AUTH0_CLI_DOMAIN=[...]
API_IDENTIFIER=[...]
```

Then can run the application and connect with API on Heroku using bash script:
```bash
$ ./run-cli.sh heroku
```

### B) Docker-compose
#### Easy way
If you want to use auth0 login, you need to create `.env` file with auth0 parameters:
```
AUTH0_CALLBACK_URL=[...]
AUTH0_CLIENT_ID=[...]
AUTH0_CLIENT_SECRET=[...]
AUTH0_DOMAIN=[...]
AUTH0_CLI_DOMAIN=[...]
API_IDENTIFIER=[...]
```
Then add SSL certificate: `web/cert.pem`, `web/key.pem`.

When running the application for the first time, provide secrets for `api` and `web`. Next time just run the script with no arguments.
```bash
$ ./run-docker-compose.sh [web secret] [api secret]
```

The command line application for couriers requires `cli/.env` file:
```
AUTH0_CLI_DOMAIN=[...]
API_IDENTIFIER=[...]
```
To start the app for couriers:
```
$ ./run-cli.sh local
```

#### Hard way
If you don't want to use the scripts, create `.env` files from 'easy way', and then add environment variables for `api` and `web` containers.
In the project folder execute commands:
```bash
$ echo "WEB_SECRET='[your secret]'" >> .env
$ echo "API_SECRET='[your secret]'" >> .env
```

Then run application with `docker-compose`:
```bash
$ docker-compose build
$ docker-compose up
```
Now you should be able to access web application: http://localhost:8000/.

To run the app for couriers execute commands:
```bash
$ docker build cli/ -t alpaczka-cli
$ docker run --network="host" -it alpaczka-cli http://localhost:8001
```

## Older releases
### P2 Setup
Create `.env` file with secret key for Flask:
```bash
$ echo "SECRET_KEY='[paste your key here]'" > .env
```

Then run the application with `docker-compose`:
```bash
$ docker-compose build
$ docker-compose up
```
Release P2 is also deployed on Heroku: https://alpaczka.herokuapp.com/.
