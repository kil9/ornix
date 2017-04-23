#!/bin/bash

APP_NAME='ornix'
APP_HOME="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd ${APP_HOME}/ornix
echo "${APP_NAME} started"
uwsgi -H ${APP_HOME}/venv -w ornix:app --http :21000 -p 4 --py-auto-reload=3
