import json
import requests
import paths
import logging

from queries import *

logging.basicConfig(filename=paths.LOG_PATH,
                    filemode='w',
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(name)s -> %(message)s')  # TODO: improve how msg is displayed
logger = logging.getLogger()

with open(paths.CONFIG_PATH, 'r') as f:
    bot_token = f.read().replace('X-Viber-Auth-Token:', '').strip()
db = DatabaseCommunication(paths.DB_PATH)


def broadcast_new_movies(diff_set):
    broadcast_msg = "(video) ```New movies in cinema this week!``` (video)\n\n"

    for new_movie in diff_set:
        broadcast_msg = broadcast_msg + "*%s*\n" % new_movie

    broadcast_list = db.fetch_all_subscribed()
    broadcast_data = {
        'type': 'text',
        'text': broadcast_msg,
        'broadcast_list': broadcast_list
    }
    resp = requests.post('https://chatapi.viber.com/pa/broadcast_message', data=json.dumps(broadcast_data),
                         headers={"X-Viber-Auth-Token": bot_token})
    if resp.text.index('"status":0') > -1:  # status:0 is a successful broadcast
        logger.info("Successfully broadcasted a message to the following users:")
        logger.info(str(broadcast_list))


broadcast_movies_result = db.fetch_broadcast_movies()

for cinema_id, cinema in broadcast_movies_result.items():
    broadcast_movies = cinema['broadcast_movies']
    if broadcast_movies is not None:
        broadcast_movies = broadcast_movies.split(';')
        broadcast_new_movies(broadcast_movies)
