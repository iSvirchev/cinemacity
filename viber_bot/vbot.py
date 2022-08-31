import datetime
import json
import logging
import requests

from queries import DatabaseCommunication
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
today = datetime_now.strftime('%d %b')
logger.info('Today is: ' + today)

db = DatabaseCommunication(paths.DB_PATH)
db.set_today_4_all(today)
logger.info('All users default date has been set to today!')

with open(paths.CONFIG_PATH, 'r') as f:
    bot_token = f.read().replace('X-Viber-Auth-Token:', '').strip()

with open(paths.MOVIES_JSON_PATH, 'r') as f:
    movies_data = json.load(f)

with open(paths.MOVIES_YESTERDAY_JSON_PATH, 'r') as f:
    movies_data_yesterday = json.load(f)

app = Flask(__name__)
viber = Api(BotConfiguration(
    name='CinemaCity',
    avatar='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSzTmbvZUpF1ocKtWIZoV9jHPQ7dXqFi0UGnA&usqp=CAU',
    auth_token=bot_token
))


def convert_arr_to_dict(arr):
    dictionary = {}
    for e in arr:
        for k, v in e.items():
            dictionary[k] = v
    return dictionary


# cast to dict() to take advantage of intellisense
days_dictionary_yesterday = dict(convert_arr_to_dict(movies_data_yesterday))

# We extract all the movies from yesterday's JSON file
yesterday_movies_set = set()
for day in days_dictionary_yesterday:
    for movie in days_dictionary_yesterday[day]:
        yesterday_movies_set.add(movie)


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


days_dictionary = dict(convert_arr_to_dict(movies_data))  # cast to dict() to take advantage of intellisense
today_movies_set = set()  # we extract ALL the movies from the whole week into this set
for day in days_dictionary:
    for movie in days_dictionary[day]:
        today_movies_set.add(movie)
        if not days_dictionary[day][movie]['movie_screenings']:  # if no movie_screenings - we want to remove the movie
            days_dictionary[day][movie].pop('poster_link')  # remove the poster_link to make the delete recursion work

days_dictionary = remove_empty_elements(days_dictionary)  # this removes movies and days with no showings (pre-sales)

rsp = Responses(days_dictionary)


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


# Return a set that contains the items that only exist in set 1, and not in set 2:
broadcast_movies_set = today_movies_set.difference(yesterday_movies_set)

if len(broadcast_movies_set) != 0:
    broadcast_new_movies(broadcast_movies_set)

days = list(days_dictionary.keys())


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

        if message.lower() == 'dates':
            viber.send_messages(sender_id, [
                TextMessage(text=rsp.dates(), keyboard=rsp.days_keyboard(days))
            ])
        elif message in days_dictionary or message.lower() == 'today' or message.lower() == 'tomorrow':
            # message here equals the date or today or tomorrow
            if message.lower() == 'today':
                sel_day = today
            elif message.lower() == 'tomorrow':
                sel_day = days[1]
            else:
                sel_day = message

            db.set_user_date(sender_id, sel_day)
            logger.info("SENDER_ID: '%s' has selected a new day: '%s'" % (sender_id, sel_day))
            try:
                reply = rsp.movies(sel_day)
                kb = rsp.movie_keyboard(sel_day)
            except KeyError as ke:
                reply = "No movie screenings for the selected day: *%s*" % sel_day
                kb = None
                logger.info(reply)

            viber.send_messages(sender_id, [
                TextMessage(text=reply, keyboard=kb)
            ])
        elif message in days_dictionary[sender_sel_date]:  # message here equals the name of the movie
            logger.info(
                "SENDER_ID: '%s' selected movie '%s' for day '%s'" % (sender_id, message, sender_sel_date))
            reply = rsp.movie(sender_sel_date, message)
            poster = days_dictionary[sender_sel_date][message]['poster_link']
            viber.send_messages(sender_id, [
                PictureMessage(text=reply, media=poster)
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
