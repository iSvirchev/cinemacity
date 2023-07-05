import json
import requests

from utility.logger import log
from utility.bot_config import bot_token
from utility.error_codes import ErrorCodes
from utility.database_comm import db

log.info("=================================================")
log.info("             Starting Broadcaster...             ")
log.info("=================================================")


def broadcast_new_movies(broadcast_set, broadcast_list, cin_name):
    broadcast_msg = "(video) ```New movies in``` *%s*(video)\n\n" % cin_name
    for new_movie in broadcast_set:
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
        log.info("Successfully broadcasted a message to the following users: %s for cinema '%s'" %
                 (str(broadcast_list), cin_name))
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


def broadcast_cinema(cinema, users_to_broadcast):
    cinema_id = cinema['cinema_id']
    cinema_name = cinema['cinema_name']
    log.info("Cinema '%s' - starting a broadcast..." % cinema_name)
    broadcasted_today = cinema['broadcasted_today']
    if not broadcasted_today:
        broadcast_movies = cinema['movies_to_broadcast']
        if broadcast_movies:
            broadcast_movies_arr = broadcast_movies.split(';')
            log.info("Cinema '%s' - movies to broadcast: %s" % (cinema_name, str(broadcast_movies)))
            # If broadcast_movies for this cinema is not empty we need check if there are any users subscribed

            if users_to_broadcast:  # Only broadcast to the subscribed users (if any)
                broadcast_new_movies(broadcast_movies_arr, users_to_broadcast, cinema_name)
            else:
                log.info("Cinema '%s' - no users subscribed to that cinema." % cinema_name)
        else:
            log.info("Cinema '%s' - nothing to broadcast!" % cinema_name)
        db.update_cinema_broadcasted_today(cinema_id, True)
        db.update_movies_to_broadcast(cinema_id, None)
    else:
        log.info("Cinema '%s' - new movies already broadcasted today!" % cinema_name)


cinemas = db.fetch_cinemas()
pulled_movies = {}  # To avoid repetitive queries about the same movie - we keep them here

for cin in cinemas.values():
    group_id = cin['group_id']
    group_cinemas = db.fetch_cinemas_by_groupId_not_broadcasted(group_id)
    nCinemas = len(group_cinemas)
    users = []
    for gr_cinema_id in group_cinemas.keys():
        test = db.fetch_subscribed_to_cinema(gr_cinema_id)
        users.extend(db.fetch_subscribed_to_cinema(gr_cinema_id))
    if nCinemas == 0:
        log.info("All the cinemas have been broadcasted!")
        break
    elif nCinemas > 1:
        log.info("There is more than one cinema in this group_id '%s' - will broadcast to the users subscribed to each "
                 "cinema in the group" % group_id)
        for gr_cinema in group_cinemas.values():
            broadcast_cinema(gr_cinema, users)
    else:
        broadcast_cinema(cin, users)
