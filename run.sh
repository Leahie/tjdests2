#!/bin/sh
dos2unix run.sh  
export PORT=8000
pipenv run gunicorn -b localhost:8000 tjdests.wsgi
