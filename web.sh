#!/bin/bash
source venv/bin/activate
source env.sh
#gunicorn ornix:app --chdir=ornix -w 2 -b ':21000' --reload
#gunicorn ornix:app --chdir=ornix -w 16 -b ':21000' -D
gunicorn ornix:app --chdir=ornix -w 4 -b ':21000'
