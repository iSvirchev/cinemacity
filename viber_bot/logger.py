import logging
import paths


def get_logger(file_name=paths.LOG_PATH):
    logger = logging.getLogger('ViberBot')
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(asctime)s] {%(filename)s:%(funcName)s():%(lineno)d} %(levelname)s -> %(message)s')
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    if file_name:
        fh = logging.FileHandler(file_name, 'a')

        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger
