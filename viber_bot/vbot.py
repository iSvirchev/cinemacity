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


rsp = Responses()
db = DatabaseCommunication(paths.DB_PATH)
db.set_today_4_all_users(today)
logger.info('All users default date has been set to today!')

with open(paths.CONFIG_PATH, 'r') as f:
    bot_token = f.read().replace('X-Viber-Auth-Token:', '').strip()

app = Flask(__name__)
viber = Api(BotConfiguration(
    name='CinemaCity',
    avatar='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSzTmbvZUpF1ocKtWIZoV9jHPQ7dXqFi0UGnA&usqp=CAU',
    auth_token=bot_token
))

cinemas = db.fetch_cinemas()

for cinema_id in cinemas:
    test = cinemas[cinema_id]['today_json']
    cinemas[cinema_id]['today_json'] = json.loads(cinemas[cinema_id]['today_json'])
    cinemas[cinema_id]['yesterday_json'] = json.loads(cinemas[cinema_id]['yesterday_json'])
    cinemas[cinema_id]['days'] = list(cinemas[cinema_id]['today_json'].keys())
movie_names = db.fetch_movies_names()
cinema_names = db.fetch_cinema_names()


def remove_empty_elements(d):
    #   recursively remove empty lists, empty dicts, or None elements from a dictionary
    def empty(x):
        return x is None or x == {} or x == []

    if not isinstance(d, (dict, list)):
        return d
    elif isinstance(d, list):
        return [v for v in (remove_empty_elements(v) for v in d) if not empty(v)]
    else:
        return {k: v for k, v in ((k, remove_empty_elements(v)) for k, v in d.items()) if not empty(v)}


for cinema_id in cinemas:
    # We extract all the movies from yesterday's JSON file
    yesterday_json = cinemas[cinema_id]['yesterday_json']
    yesterday_movies_set = set()
    for day in yesterday_json:
        for movie_id, movie in yesterday_json[day].items():
            yesterday_movies_set.add(movie['movie_name'])

    today_json = cinemas[cinema_id]['today_json']
    today_movies_set = set()  # we extract ALL the movies from the whole week into this set
    for day in today_json:
        for movie_id, movie in today_json[day].items():
            today_movies_set.add(movie['movie_name'])
            if not movie['movie_screenings']:  # if no movie_screenings - we remove the movie
                # remove the booking_link to make the delete recursion work
                movie.pop('booking_link')
                # remove the movie_name to make the delete recursion work
                movie.pop('movie_name')
    today_json = remove_empty_elements(today_json)  # removes movies and days with no showings - (pre-sales)
    db.update_today_jsons(cinema_id, json.dumps(today_json))

    # Return a set that contains the items that only exist in set 1, and not in set 2:
    broadcast_movies_set = today_movies_set.difference(yesterday_movies_set)

    if len(broadcast_movies_set) != 0:
        db.update_broadcast_movies(cinema_id, ';'.join(broadcast_movies_set))


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

        sender_sel_date = db.fetch_user_date(sender_id)
        sender_sel_cinema = db.fetch_user_cinema(sender_id)

        if message in cinema_names:
            user_cinema_id = db.fetch_cinema_by_name(message, 0)
            db.set_user_cinema(sender_id, user_cinema_id)
            viber.send_messages(sender_id, [
                TextMessage(text="You have chosen *%s* as your favourite cinema!\n\n%s" % (message, rsp.info))
            ])
        elif message.lower() == 'cinema' or message.lower() == 'cinemas' or sender_sel_cinema is None:
            viber.send_messages(sender_id, [
                TextMessage(text="Please pick a cinema first.", keyboard=rsp.cinemas_keyboard(cinemas))
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
                reply = rsp.movies(sel_day)
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
            r = 'Screenings of movie *%s* on *%s* in cinema *%s*\n\n' % (message, sender_sel_date, cinema_name)
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
