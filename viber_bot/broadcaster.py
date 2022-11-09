import json
import requests
import paths
import logger

from error_codes import ErrorCodes

from queries import *

log = logger.get_logger()
log.info("=================================================")
log.info("             Starting Broadcaster...             ")
log.info("=================================================")
db = DatabaseCommunication(paths.DB_PATH)

with open(paths.TOKEN_FILE_PATH, 'r') as f:
    bot_token = f.read().replace('X-Viber-Auth-Token:', '').strip()
log.info("bot_token extracted")


def broadcast_new_movies(diff_set, broadcast_list, cin_name):
    broadcast_msg = "(video) ```New movies in ```*%s*``` this week!``` (video)\n\n" % cin_name
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


cinemas = db.fetch_cinemas()
for cinema_id, cinema in cinemas.items():
    cinema_db = db.fetch_cinema_by_id(cinema_id)
    cinema_name = cinema_db[CinemasTable.CINEMA_NAME]
    movies_today = cinema_db[CinemasTable.MOVIES_TODAY].split(';')
    movies_yesterday = cinema_db[CinemasTable.MOVIES_YESTERDAY].split(';')
    broadcasted_today = cinema_db[CinemasTable.BROADCASTED_TODAY]

    if not broadcasted_today:
        m_today_set = set(movies_today)
        m_yesterday_set = set(movies_yesterday)

        diff_set = m_today_set.difference(m_yesterday_set)
        broadcast_movies = []
        for m_id in diff_set:
            m_name = db.fetch_movie_by_id(m_id)[MoviesTable.MOVIE_NAME]
            broadcast_movies.append(m_name)
        log.info("Cinema '%s' - movies to broadcast: %s" % (cinema_name, str(broadcast_movies)))
        if broadcast_movies:
            # If broadcast_movies for this cinema is not empty we need check if there are any users subscribed
            users_to_broadcast = db.fetch_subscribed_to_cinema(cinema_id)
            # TODO: Sofia has 2 cinemas - if user is subscribed to either one of them - they should be notified for both
            # TODO: use 'groupId' from API
            if users_to_broadcast:  # Only broadcast to the subscribed users (if any)
                log.info("Cinema '%s' - starting a broadcast..." % cinema_name)
                broadcast_new_movies(broadcast_movies, users_to_broadcast, cinema_name)
            else:
                log.info("Cinema '%s' - no users subscribed to that cinema." % cinema_name)
        else:
            log.info("Cinema '%s' - nothing to broadcast!" % cinema_name)
        db.update_cinema_broadcasted_today(cinema_id, True)
    else:
        log.info("Cinema '%s' - new movies already broadcasted today!" % cinema_name)
