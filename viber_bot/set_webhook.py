from utility.logger import log
from utility.bot_config import viber_bot


log.info("Will try to set the webhook...")
test = viber_bot.set_webhook('https://theclumsybarber.party/vbot')
log.info("Successfully set the new webhook!")
