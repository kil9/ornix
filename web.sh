#!/bin/bash
source venv/bin/activate
source env.sh
gunicorn ornix:app --chdir=ornix -w 2 -b ':21000' --reload
