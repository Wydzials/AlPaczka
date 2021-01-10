#!/bin/bash

if [[ -n $1 && -n $2 ]]; then
	echo "WEB_SECRET='$1'" >> .env
	echo "API_SECRET='$2'" >> .env
fi

if ! grep -q "WEB_SECRET=" ".env" || ! grep -q "API_SECRET=" ".env"; then
	echo "Secrets not found in .env, so two arguments are required: WEB_SECRET and API_SECRET"
	exit
fi

docker-compose build
docker-compose up
