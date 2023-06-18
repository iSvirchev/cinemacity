import sys
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


def log_uncaught(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    log.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = log_uncaught
