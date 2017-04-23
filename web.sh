#!/bin/bash
source venv/bin/activate
gunicorn ornix:app --chdir=ornix -w 2 -b ':21000' --reload
