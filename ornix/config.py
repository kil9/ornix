import os
import sys
import logging
from logentries import LogentriesHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine

APP_HOME = '/ornix'
APP_NAME = 'ornix'

LOGENTRIES_KEY = os.environ['LOGENTRIES_KEY']
DATABASE_URL = os.environ['DATABASE_URL']
#DATABASE_URL = 'mysql+pymysql://ornix@localhost/ornix?charset=utf8'

LOG_FORMAT = '%(asctime)s [%(levelname)s] %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format=LOG_FORMAT)
log = logging.getLogger(__name__)

#lh = logging.FileHandler('{}/var/logs/{}.log'.format(APP_HOME, APP_NAME))
#log.addHandler(lh)

log.addHandler(LogentriesHandler(LOGENTRIES_KEY))

app = Flask(APP_NAME)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
