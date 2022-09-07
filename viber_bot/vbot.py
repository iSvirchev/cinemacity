import datetime
import json
import logging

from queries import *
from responses import Responses
import paths

from flask import Flask, request, Response
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages import *
from viberbot.api.viber_requests import ViberConversationStartedRequest, ViberFailedRequest, ViberMessageRequest, \
    ViberSubscribedRequest

logging.basicConfig(filename=paths.LOG_PATH,
                    filemode='w',
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(name)s -> %(message)s')  # TODO: improve how msg is displayed
logger = logging.getLogger()

datetime_now = datetime.datetime.now()
tomorrow_datetime = datetime_now + datetime.timedelta(days=1)
today = datetime_now.strftime('%d %b')
tomorrow = tomorrow_datetime.strftime('%d %b')
logger.info('Today is: ' + today)
logger.info('Tomorrow is: ' + tomorrow)

rsp = Responses()
db = DatabaseCommunication(paths.DB_PATH)
db.set_today_4_all_users(today)
logger.info('All users\' default dates have been set to today!')

with open(paths.CONFIG_PATH, 'r') as f:
    bot_token = f.read().replace('X-Viber-Auth-Token:', '').strip()
logger.info("bot_token extracted")

app = Flask(__name__)
viber = Api(BotConfiguration(
    name='CinemaCity',
    avatar='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSzTmbvZUpF1ocKtWIZoV9jHPQ7dXqFi0UGnA&usqp=CAU',
    auth_token=bot_token
))

cinemas = db.fetch_cinemas()
logger.info("cinemas has been initialized.")


def remove_empty_elements(d):  # recursively remove empty lists, empty dicts, or None elements from a dictionary

    def empty(x):
        return x is None or x == {} or x == []

    if not isinstance(d, (dict, list)):
        return d
    elif isinstance(d, list):
        return [v for v in (remove_empty_elements(v) for v in d) if not empty(v)]
    else:
        return {k: v for k, v in ((k, remove_empty_elements(v)) for k, v in d.items()) if not empty(v)}

logger.info("--------------------------------------------------------------")
for cinema_id, cinema in cinemas.items():
    logger.info("Processing data for cinema_id %s with name %s" % (cinema_id, cinema['cinema_name']))
    today_json = json.loads(cinema['today_json'])
    # on first run db's yesterday_json is empty - we assign today_json
    yesterday_json = json.loads(cinema['yesterday_json']) if cinema['yesterday_json'] is not None else today_json
    cinema['today_json'] = today_json
    cinema['yesterday_json'] = yesterday_json
    cinema['days'] = list(cinema['today_json'].keys())

    yesterday_movies_set = set()  # we extract all the movies from yesterday's JSON file
    today_movies_set = set()  # we extract ALL the movies from the whole week into this set

    for day in yesterday_json:
        for movie_id, movie in yesterday_json[day].items():
            yesterday_movies_set.add(movie['movie_name'])
    logger.info("All movies from yesterday_json have been extracted.")

    for day in today_json:
        for movie_id, movie in today_json[day].items():
            today_movies_set.add(movie['movie_name'])
            if not movie['movie_screenings']:  # if no movie_screenings - we remove the movie
                # remove the booking_link to make the delete recursion work
                movie.pop('booking_link')
                # remove the movie_name to make the delete recursion work
                movie.pop('movie_name')
    logger.info("All movies from today_json have been extracted - today_movies_set len is: %s" % len(today_json))
    today_json = remove_empty_elements(today_json)  # removes movies and days with no showings - (pre-sales)
    logger.info("today_movies_set len after remove_empty_elements is: %s" % len(today_json))
    db.update_today_jsons(cinema_id, json.dumps(today_json))

    # Return a set that contains the items that only exist in set 1, and not in set 2:
    diff_set = today_movies_set.difference(yesterday_movies_set)

    if len(diff_set) != 0:  # if the difference set's size is bigger tha 0 - we set cinemas.broadcast_movies to diff_set
        logger.info("diff_set is not empty for cinema %s" % cinema_id)
        logger.info("diff_set is: %s" % diff_set)
        db.update_broadcast_movies(cinema_id, ';'.join(diff_set))
    logger.info("--------------------------------------------------------------")

movie_names = db.fetch_movies_names()
logger.info("movie_names has been initialized.")
cinema_names = db.fetch_cinema_names()
logger.info("cinema_names has been initialized.")


@app.route('/', methods=['POST'])
def incoming():
    logger.debug("Received request! Post data: {0}".format(request.get_data()))
    # every viber message is signed, you can verify the signature using this method
    if not viber.verify_signature(request.get_data(), request.headers.get('X-Viber-Content-Signature')):
        return Response(status=403)

    viber_request = viber.parse_request(request.get_data())

    if isinstance(viber_request, ViberMessageRequest):
        sender_name = viber_request.sender.name
        sender_id = viber_request.sender.id

        message = viber_request.message.text
        logger.info("MSG received: '%s' from SENDER_ID: '%s'" % (message, sender_id))
        db.add_user(sender_id, sender_name, today)

        sender_sel_cinema = db.fetch_user(sender_id)[UsersTable.selected_cinema_id.value]
        sender_sel_date = db.fetch_user(sender_id)[UsersTable.selected_date.value]

        if message.lower() == 'sub' or message.lower() == 'unsub':
            is_subscribed = db.fetch_user(sender_id)[UsersTable.subscribed.value]
            sub_msg = 'An issue occurred...'
            if not is_subscribed and message.lower() == 'sub':
                db.update_user_subscription_status(sender_id, 1)
                sub_msg = 'You are now *SUBSCRIBED* to our cinema updates.\nType "*unsub*" if you wish to unsubscribe.'
            elif not is_subscribed and message.lower() == 'unsub':
                sub_msg = 'You cannot unsubscribe because you are currently not subscribed.\nType "*sub*" to subscribe to our updates!'
            if is_subscribed and message.lower() == 'sub':
                sub_msg = 'You are already subscribed.\nType "*unsub*" if you wish to unsubscribe'
            if is_subscribed and message.lower() == 'unsub':
                db.update_user_subscription_status(sender_id, 0)
                sub_msg = 'You are now *UNSUBSCRIBED* from our cinema updates.\nType "*sub*" if you wish to subscribe again'
            viber.send_messages(sender_id, [
                TextMessage(text=sub_msg)])
        elif message in cinema_names:
            user_cinema_id = db.fetch_cinema_by_name(message, 0)
            db.set_user_cinema(sender_id, user_cinema_id)
            viber.send_messages(sender_id, [
                TextMessage(text="You have chosen *%s* as your favourite cinema!\n\n%s" % (message, rsp.info))
            ])
        elif message.lower() == 'cinema' or message.lower() == 'cinemas' or sender_sel_cinema is None:
            viber.send_messages(sender_id, [
                TextMessage(text="Please pick your favourite cinema so we can begin",
                            keyboard=rsp.cinemas_keyboard(cinemas))
            ])
        elif message.lower() == 'dates':
            viber.send_messages(sender_id, [
                TextMessage(text=rsp.dates(), keyboard=rsp.days_keyboard(cinemas[sender_sel_cinema]['days']))
            ])
        elif message in today_json or message.lower() == 'today' or message.lower() == 'tomorrow':
            # message here equals the date or today or tomorrow
            if message.lower() == 'today':
                sel_day = today
            elif message.lower() == 'tomorrow':
                sel_day = tomorrow
            else:
                sel_day = message

            db.set_user_date(sender_id, sel_day)
            logger.info("SENDER_ID: '%s' has selected a new day: '%s'" % (sender_id, sel_day))
            try:
                reply = rsp.movies(sel_day, cinemas[sender_sel_cinema]['cinema_name'])
                kb = rsp.movie_keyboard(cinemas[sender_sel_cinema]['today_json'][sel_day])
            except KeyError as ke:
                reply = "No movie screenings for the selected day: *%s*" % sel_day
                kb = None
                logger.info(reply)

            viber.send_messages(sender_id, [
                TextMessage(text=reply, keyboard=kb)
            ])
        elif message in movie_names:  # message here equals the name of the movie
            logger.info(
                "SENDER_ID: '%s' selected movie '%s' for day '%s for cinema %s'" % (
                    sender_id, message, sender_sel_date, sender_sel_cinema))
            movie_id = db.fetch_movie_by_name(message, MoviesTable.movie_id.value)
            screenings = cinemas[sender_sel_cinema]['today_json'][sender_sel_date][movie_id]['movie_screenings']
            cinema_name = cinemas[sender_sel_cinema]['cinema_name']
            base_movie_url = db.fetch_movie_by_id(movie_id, MoviesTable.movie_link.value)
            resp_url = "%s#/buy-tickets-by-film?in-cinema=%s" % (base_movie_url, sender_sel_cinema)
            # TODO: This should work, but '?' query string separator breaks the URI - wait for viber support's response
            viber.send_messages(sender_id, [
                URLMessage(media=resp_url)
            ])
            r = 'Screenings of movie *%s* on *%s* in *%s*\n\n' % (message, sender_sel_date, cinema_name)
            r = r + '\n'.join(screenings)
            viber.send_messages(sender_id, [
                TextMessage(text=r)
            ])
        else:
            viber.send_messages(sender_id, [
                TextMessage(text=rsp.info)
            ])
    elif isinstance(viber_request, ViberSubscribedRequest):
        viber.send_messages(viber_request.user.id, [
            TextMessage(text='Hello %s! Thanks you for subscribing!\n'
                             'Type *INFO* for more information on the available commands.' % viber_request.user.name)
        ])
    elif isinstance(viber_request, ViberConversationStartedRequest):
        reply = 'Welcome %s!\n\n%s' % (viber_request.user.name, rsp.info)
        viber.send_messages(viber_request.user.id, [
            TextMessage(text=reply)
        ])
    elif isinstance(viber_request, ViberFailedRequest):
        print("Failed!")

    return Response(status=200)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
