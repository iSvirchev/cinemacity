import os
from from_root import from_root

ROOT_DIR = from_root()

LOG_PATH = os.path.join(ROOT_DIR, 'viber_bot', 'logs', 'vbot.log')
DB_PATH = os.path.join(ROOT_DIR, 'vbot.db')
TOKEN_FILE_PATH = os.path.join(ROOT_DIR, 'viber_bot', 'misc', 'token_file')
MOCKED_CINEMAS_PATH = os.path.join(ROOT_DIR, 'viber_bot', 'misc', 'mocked_cinemas.json')