import json
import requests
import paths
import logging
from error_codes import ErrorCodes

from queries import *

logger = logging.getLogger()
logging.basicConfig(filename=paths.LOG_PATH,
                    filemode='a',
                    level=logging.INFO,
                    format='[%(asctime)s] {%(filename)s:%(funcName)s():%(lineno)d} %(levelname)s -> %(message)s')
handler = logging.StreamHandler()
logger.addHandler(handler)

db = DatabaseCommunication(paths.DB_PATH)

with open(paths.CONFIG_PATH, 'r') as f:
    bot_token = f.read().replace('X-Viber-Auth-Token:', '').strip()
logger.info("bot_token extracted")


def broadcast_new_movies(diff_set, broadcast_list, cin_id):
    logger.info("Starting a broadcast...")
    cinema_name = db.fetch_cinema_by_id(cin_id, CinemasTable.CINEMA_NAME)
    broadcast_msg = "(video) ```New movies in ```*%s*``` this week!``` (video)\n\n" % cinema_name

    for new_movie in diff_set:
        broadcast_msg = broadcast_msg + "*%s*\n" % new_movie

    broadcast_data = {
        'type': 'text',
        'text': broadcast_msg,
        'broadcast_list': broadcast_list
    }
    resp = requests.post('https://chatapi.viber.com/pa/broadcast_message', data=json.dumps(broadcast_data),
                         headers={"X-Viber-Auth-Token": bot_token})

    resp_json = resp.json()
    status_msg = resp_json['status']

    if status_msg == ErrorCodes.OK:
        logger.info("Successfully broadcasted a message to the following users: %s", str(broadcast_list))
    else:
        failed_list = resp_json['failed_list'][0]
        failed_user_id = failed_list['receiver']
        failed_status_code = failed_list['status']
        failed_status_msg = failed_list['status_message']
        logger.info("Broadcasting failed for the following user: %s, status_code: %s, reason: %s" % (
            failed_user_id, failed_status_code, failed_status_msg))
        if failed_status_code == ErrorCodes.RECEIVER_NOT_SUBSCRIBED:
            logger.info(
                "User is not subscribed to the Viber Bot - will unsubscribe the user from the new movie newsletter.")
            db.update_user_subscription_status(failed_user_id, 0)
            logger.info("%s was unsubscribed from the newsletter successfully.", failed_user_id)


broadcast_movies_result = db.fetch_broadcast_movies()
logger.info("Extracting movies to broadcast")
for cinema_id, cinema in broadcast_movies_result.items():
    broadcast_movies = cinema['broadcast_movies']
    if broadcast_movies is not None:
        broadcast_movies = broadcast_movies.split(';')
        # If broadcast_movies for this cinema is not NULL we need check if there are any users subscribed
        users_to_broadcast = db.fetch_subscribed_users(cinema_id)
        # TODO: Sofia has 2 cinemas - if user is subscribed to either one of them - they should be notified for both
        # TODO: use 'groupId' from API
        if users_to_broadcast:  # Only broadcast to the subscribed users (if any)
            broadcast_new_movies(broadcast_movies, users_to_broadcast, cinema_id)
    logger.info("Broadcasting has finished for '%s'. Resetting broadcast_movies for that cinema...",
                cinema['cinema_name'])
    # db.reset_broadcast_movies(cinema_id)
    logger.info("cinemas.broadcast_movies for '%s' has been reset!", cinema['cinema_name'])
