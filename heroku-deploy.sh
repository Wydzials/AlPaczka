#!/bin/bash

function commit_push() {
	git add .
	git commit -m "$1"
	git push heroku master
}

if [[ -z $1 ]]; then
	echo "Commit name cannot be empty."
	exit
fi

cd api
commit_push $1

cd ../web
commit_push $1

echo "Commit '$1' deployed on Heroku."
