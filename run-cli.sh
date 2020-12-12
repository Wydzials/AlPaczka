#!/bin/bash

if [[ $1 == "heroku" ]]; then
	token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE2MTY0NTMxODQsImlhdCI6MTYwNzgxMzE4NCwic3ViIjoiQ09VUklFUiJ9.28--2DlGSrCQod2HULZIv13XSb5svGrZr_LFO1L7fMc"
	api="https://alpaczka-api.herokuapp.com"
elif [[ $1 == "local" ]]; then
	token=$(python3 api_token_generator.py)
	api="http://0.0.0.0:8001"
else
	echo "API argument required: 'heroku' or 'local'"
	exit
fi

echo "TOKEN='$token'" > cli/.env
echo "API_URL='$api'" >> cli/.env

docker build cli/ -t alpaczka-cli
docker run --network="host" -it alpaczka-cli
