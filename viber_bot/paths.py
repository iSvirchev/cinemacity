from sys import platform


LOG_PATH = 'logs/vbot.log'
DB_PATH = '../vbot.db'
CONFIG_PATH = 'misc/token_file'

if platform == "win32":  # Using this for local work
    CONFIG_PATH = CONFIG_PATH.replace('/', '\\')
    DB_PATH = DB_PATH.replace('/', '\\')
    LOG_PATH = LOG_PATH.replace('/', '\\')
