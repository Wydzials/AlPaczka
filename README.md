# AlPaczka (AlPackage)

### General info
Flask web application for modern package delivery system.

### Setup
To run this project, first you need to create `.env` file with secret key for Flask:
```
echo "SECRET_KEY='[paste your key here]'" > .env
```

Then run application with `docker-compose`:
```
docker-compose build
docker-compose up
```

### Heroku
Release P2 is also deployed on Heroku: https://alpaczka.herokuapp.com/
