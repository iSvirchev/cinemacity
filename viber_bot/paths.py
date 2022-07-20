from sys import platform


DB_PATH = 'misc/vbot.db'
CONFIG_PATH = 'misc/token_file'
MOVIES_JSON_PATH = '../cinemacity_crawlers/movies.json'
MOVIES_YESTERDAY_JSON_PATH = '../cinemacity_crawlers/movies_yesterday.json'

if platform == "win32":  # Using this for local work
    CONFIG_PATH = CONFIG_PATH.replace('/', '\\')
    MOVIES_JSON_PATH = MOVIES_JSON_PATH.replace('/', '\\')
    MOVIES_YESTERDAY_JSON_PATH = MOVIES_YESTERDAY_JSON_PATH.replace('/', '\\')
    DB_PATH = DB_PATH.replace('/', '\\')
