from viberbot.api.bot_configuration import BotConfiguration
from viberbot import Api
from utility.database_comm import db

bot_token = db.fetch_config_value('token')

viber_bot = Api(BotConfiguration(
    name='CinemaCity',
    avatar='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSzTmbvZUpF1ocKtWIZoV9jHPQ7dXqFi0UGnA&usqp=CAU',
    auth_token=bot_token
))
