from viberbot.api.bot_configuration import BotConfiguration
from viberbot import Api
from utility.paths import TOKEN_FILE_PATH

with open(TOKEN_FILE_PATH, 'r') as f:
    bot_token = f.read().replace('X-Viber-Auth-Token:', '').strip()

viber_bot = Api(BotConfiguration(
    name='CinemaCity',
    avatar='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSzTmbvZUpF1ocKtWIZoV9jHPQ7dXqFi0UGnA&usqp=CAU',
    auth_token=bot_token
))
