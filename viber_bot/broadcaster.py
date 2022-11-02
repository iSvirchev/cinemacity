import json
import requests
import paths
import logger

from error_codes import ErrorCodes

from queries import *

log = logger.get_logger()

db = DatabaseCommunication(paths.DB_PATH)

with open(paths.TOKEN_FILE_PATH, 'r') as f:
    bot_token = f.read().replace('X-Viber-Auth-Token:', '').strip()
log.info("bot_token extracted")


def broadcast_new_movies(diff_set, broadcast_list, cin_name):
    broadcast_msg = "(video) ```New movies in ```*%s*``` this week!``` (video)\n\n" % cin_name
    log.info("Movies to broadcast: %s", str(diff_set))
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
    failed_list = resp_json['failed_list']
    log.info("Broadcast failed for %d users!", len(failed_list))
    if len(failed_list) == 0:
        log.info("Successfully broadcasted a message to the following users: %s", str(broadcast_list))
    else:
        for failed_user in failed_list:
            failed_user_id = failed_user['receiver']

            failed_status_code = failed_user['status']
            failed_status_msg = failed_user['status_message']
            log.warning("Broadcast failed for user: %s, status_code: %s, reason: %s" % (
                failed_user_id, failed_status_code, failed_status_msg))
            if failed_status_code == ErrorCodes.RECEIVER_NOT_SUBSCRIBED:
                log.info(
                    "User is not subscribed to the Viber Bot - will unsubscribe the user from the new movies "
                    "newsletter.")
                db.update_user_subscription_status(failed_user_id, False)
                log.info("'%s' was unsubscribed from the newsletter successfully.", failed_user_id)
            else:
                log.error("Problem with broadcasting to '%s' check status_message: '%s'" % (
                    failed_user_id, failed_status_msg))


broadcast_movies_result = db.fetch_broadcast_movies()
log.info("Extracting movies to broadcast")
for cinema_id, cinema in broadcast_movies_result.items():
    cinema_name = cinema['cinema_name']
    broadcast_movies = cinema['broadcast_movies']
    if broadcast_movies is not None:
        broadcast_movies = broadcast_movies.split(';')
        # If broadcast_movies for this cinema is not NULL we need check if there are any users subscribed
        users_to_broadcast = db.fetch_subscribed_to_cinema(cinema_id)
        # TODO: Sofia has 2 cinemas - if user is subscribed to either one of them - they should be notified for both
        # TODO: use 'groupId' from API
        if users_to_broadcast:  # Only broadcast to the subscribed users (if any)
            log.info("Cinema '%s' - starting a broadcast...", cinema_name)
            broadcast_new_movies(broadcast_movies, users_to_broadcast, cinema_name)
        else:
            log.info("Cinema '%s' - no users subscribed to that cinema.", cinema_name)
        log.info("Cinema '%s' - broadcast has finished. Resetting broadcast_movies for that cinema...",
                 cinema_name)
        db.reset_broadcast_movies(cinema_id)
        log.info("Cinema '%s' - cinemas.broadcast_movies has been reset!", cinema_name)
    else:
        log.info("Cinema '%s' - nothing to broadcast!", cinema_name)
