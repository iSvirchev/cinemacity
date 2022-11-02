from sys import platform


LOG_PATH = 'logs/vbot.log'
DB_PATH = '../vbot.db'
MISC_PATH = 'misc/'
TOKEN_FILE_PATH = MISC_PATH + 'token_file'

if platform == "win32":  # Using this for local work
    TOKEN_FILE_PATH = TOKEN_FILE_PATH.replace('/', '\\')
    DB_PATH = DB_PATH.replace('/', '\\')
    LOG_PATH = LOG_PATH.replace('/', '\\')
