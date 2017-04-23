import logging

LOG_FORMAT = '%(asctime)s [%(levelname)s] %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format=LOG_FORMAT)

log = logging.getLogger(__name__)
log.addHandler(LogentriesHandler(LOGENTRIES_KEY))
