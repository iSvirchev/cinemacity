import os
from utility.logger import log
from utility.bot_config import viber_bot

TOKEN_FILE = os.path.join(os.path.dirname(__file__), 'misc', 'token_file.txt')

with open(TOKEN_FILE, 'r') as f:
    TOKEN = f.read().strip()

webhook = TOKEN.strip() + ('/vbot')

log.info("Will try to set the webhook to... " + webhook)
test = viber_bot.set_webhook(webhook)
log.info("Successfully set the new webhook!")
