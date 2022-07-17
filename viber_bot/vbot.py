import datetime
import json
import logging
from sys import platform
from user_func import DatabaseCommunication

from flask import Flask, request, Response
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages import *
from viberbot.api.viber_requests import ViberConversationStartedRequest, ViberFailedRequest, ViberMessageRequest, \
    ViberSubscribedRequest

logging.basicConfig(filename='vbot.log',
                    filemode='w',
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(name)s -> %(message)s')  # TODO: improve how msg is displayed
logger = logging.getLogger()

DB_PATH = 'misc/vbot.db'
CONFIG_PATH = 'misc/token_file'
MOVIES_JSON_PATH = '../cinemacity_crawlers/movies.json'
MOVIES_YESTERDAY_JSON_PATH = '../cinemacity_crawlers/movies_yesterday.json'

logger.info('OS is: ' + platform)
if platform == "win32":  # Using this for local work
    CONFIG_PATH = CONFIG_PATH.replace('/', '\\')
    MOVIES_JSON_PATH = MOVIES_JSON_PATH.replace('/', '\\')
    MOVIES_YESTERDAY_JSON_PATH = MOVIES_YESTERDAY_JSON_PATH.replace('/', '\\')
    DB_PATH = DB_PATH.replace('/', '\\')

datetime_now = datetime.datetime.now()
today = datetime_now.strftime('%d %b')
logger.info('Today is: ' + today)

db = DatabaseCommunication(DB_PATH)
db.set_today_4_all(today)
logger.info('All users default date has been set to today!')

f1 = open(CONFIG_PATH, 'r')
bot_token = f1.read().replace('X-Viber-Auth-Token:', '').strip()
f1.close()

f2 = open(MOVIES_JSON_PATH)
movies_data = json.load(f2)
f2.close()

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

for day in days_dictionary:
    for movie in days_dictionary[day]:
        if not days_dictionary[day][movie]['movie_screenings']:  # if no movie_screenings - we want to remove the movie
            days_dictionary[day][movie].pop('poster_link')  # remove the poster_link to make the delete recursion work
days_dictionary = remove_empty_elements(days_dictionary)

days = list(days_dictionary.keys())

dates_resp = 'Which day are you interested in?\n'
for day_resp in days_dictionary:
    dates_resp = dates_resp + '\n' + day_resp


def generate_movies_response(movies_resp_day):
    movies_resp = '*Movies currently in cinema for date %s*\n' % movies_resp_day
    for movie_resp in days_dictionary[movies_resp_day]:
        movies_resp = movies_resp + '\n' + movie_resp
    return movies_resp


info_resp = 'Please type one of the following commands:\n\n' \
            '*Today* - will display today\'s movies on screen\n' \
            '*Tomorrow* - will display tomorrow\'s movies on screen\n' \
            '*Dates* - will provide you with buttons of dates from which you can choose.'


def generate_btn_keyboard(days_arr):
    keyboard = {
        "Type": "keyboard",
        "Buttons": []
    }

    colour_codes = ['#75ace1', '#df7779', '#d1b185', '#8187d5', '#00703c', '#7ac2dc', '#bc8dc9', '#727C96', '#D9CBC1',
                    '#75ace1', '#df7779', '#d1b185', '#8187d5', '#00703c', '#7ac2dc', '#bc8dc9', '#727C96', '#D9CBC1',
                    '#75ace1', '#df7779', '#d1b185', '#8187d5', '#00703c', '#7ac2dc', '#bc8dc9', '#727C96', '#D9CBC1']

    button_tpl = {
        "Columns": 2,
        "Rows": 2,
        "BgColor": "#e6f5ff",  # <enter_colour_code_here>
        "BgLoop": True,
        "ActionType": "reply",
        "ActionBody": "<add_action_body>",
        "Text": "<add_btn_txt>"
    }
    for day in days_arr:
        day_btn = button_tpl.copy()  # we use .copy() as a simple assignment operator '=' gives us object reference
        day_btn['ActionBody'] = day
        day_btn['Text'] = '<font size=\"24\">%s</font>' % day
        day_btn['BgColor'] = colour_codes[days_arr.index(day)]
        keyboard['Buttons'].append(day_btn)

    return keyboard


days_kb = generate_btn_keyboard(days)


def generate_movie_keyboard(movie_kb_day):
    keyboard = {
        "Type": "keyboard",
        "Buttons": []
    }

    m_btn_tpl = {
        "Columns": 2,
        "Rows": 2,
        "BgColor": "#e6f5ff",
        "BgLoop": True,
        "BgMedia": "<add_poster_link>",
        "ActionType": "",
        "ActionBody": "<add_action_body>",
        "Text": "<add_btn_txt>"
    }

    for m_name, m_value in days_dictionary[movie_kb_day].items():
        m_poster = m_value['poster_link']

        day_btn = m_btn_tpl.copy()  # we use .copy() as a simple assignment operator '=' gives us object reference
        day_btn['ActionBody'] = m_name
        # day_btn['Text'] = "<font size=\"12\">%s</font>" % m_name
        day_btn['Text'] = m_name
        day_btn['BgMedia'] = m_poster
        keyboard['Buttons'].append(day_btn)

    return keyboard


def gen_movie_resp(movie_resp_day, movie_resp_movie):
    m_resp = 'Screenings of movie *%s* on *%s*\n\n' % (movie_resp_movie, movie_resp_day)
    screenings = days_dictionary[movie_resp_day][movie_resp_movie]['movie_screenings']
    m_resp = m_resp + '\n'.join(screenings)
    return m_resp


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
                TextMessage(text=dates_resp, keyboard=days_kb)
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
                reply = generate_movies_response(sel_day)
                kb = generate_movie_keyboard(sel_day)
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
            reply = gen_movie_resp(sender_sel_date, message)
            poster = days_dictionary[sender_sel_date][message]['poster_link']
            viber.send_messages(sender_id, [
                PictureMessage(text=reply, media=poster)
            ])
        else:
            viber.send_messages(sender_id, [
                TextMessage(text=info_resp)
            ])
    elif isinstance(viber_request, ViberSubscribedRequest):
        viber.send_messages(viber_request.user.id, [
            TextMessage(text='Hello %s! Thanks you for subscribing!\n'
                             'Type *INFO* for more information on the available commands.' % viber_request.user.name)
        ])
    elif isinstance(viber_request, ViberConversationStartedRequest):
        reply = 'Welcome %s!\n\n%s' % (viber_request.user.name, info_resp)
        viber.send_messages(viber_request.user.id, [
            TextMessage(text=reply)
        ])
    elif isinstance(viber_request, ViberFailedRequest):
        print("Failed!")

    return Response(status=200)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
