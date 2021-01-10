#!/bin/bash

if [[ $1 == "heroku" ]]; then
	api="https://alpaczka-api.herokuapp.com"
elif [[ $1 == "local" ]]; then
	api="http://0.0.0.0:8001"
else
	echo "API argument required: 'heroku' or 'local'"
	exit
fi

docker build cli/ -t alpaczka-cli
docker run --network="host" -it alpaczka-cli $api
