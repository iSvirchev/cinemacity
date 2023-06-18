import logging
from utility.paths import LOG_PATH

log = logging.getLogger('ViberBot')
log.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] {%(filename)s:%(funcName)s():%(lineno)d} %(levelname)s -> %(message)s')
sh = logging.StreamHandler()
sh.setFormatter(formatter)
log.addHandler(sh)

if LOG_PATH:
    fh = logging.FileHandler(LOG_PATH, 'a', 'utf-8')

    fh.setFormatter(formatter)
    log.addHandler(fh)
