from flask import Flask, request, Response
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages import *
import logging

import json

from viberbot.api.viber_requests import ViberConversationStartedRequest
from viberbot.api.viber_requests import ViberFailedRequest
from viberbot.api.viber_requests import ViberMessageRequest
from viberbot.api.viber_requests import ViberSubscribedRequest
from viberbot.api.viber_requests import ViberUnsubscribedRequest


def init_logger():
    global logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


init_logger()


def load_json_data(path):
    file = open(path)
    file_data = json.load(file)
    file.close()

    return file_data


config_data = load_json_data('misc\\config.json')
movies_data = load_json_data('..\\cinemacity_crawlers\\movies.json')

app = Flask(__name__)
viber = Api(BotConfiguration(
    name='CinemaCity',
    avatar='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSzTmbvZUpF1ocKtWIZoV9jHPQ7dXqFi0UGnA&usqp=CAU',
    auth_token=config_data['bot_token']
))


def convert_arr_to_dict(arr):
    dict = {}
    for e in arr:
        for k, v in e.items():
            dict[k] = v

    return dict


movies_data = dict(convert_arr_to_dict(movies_data))  # use dict() to take advantage of intellisense

days = list(movies_data.keys())
dates_resp = 'Which day are you interested in?\n'
for data in movies_data:
    dates_resp = dates_resp + '\n' + data

TODAY = days[0]


def generate_movies_response(day):
    movies_resp = '*Movies currently in cinema for date %s*\n' % day
    for movie in movies_data[day]:
        movies_resp = movies_resp + '\n' + movie
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
                    '#EDE7DC', '#C9CBD0', '#ECE3E0']

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


def generate_movie_keyboard(day):
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

    for m_name, m_value in movies_data[day].items():
        m_poster = m_value['poster_link']

        day_btn = m_btn_tpl.copy()  # we use .copy() as a simple assignment operator '=' gives us object reference
        day_btn['ActionBody'] = m_name
        # day_btn['Text'] = "<font size=\"12\">%s</font>" % m_name
        day_btn['Text'] = m_name
        day_btn['BgMedia'] = m_poster
        keyboard['Buttons'].append(day_btn)

    return keyboard


def gen_movie_resp(day, movie):
    m_resp = 'Screenings of movie *%s* on *%s*\n\n' % (movie, day)
    screenings = movies_data[day][movie]['movie_screenings']
    m_resp = m_resp + '\n'.join(screenings)
    return m_resp


selected_day = TODAY


@app.route('/', methods=['POST'])
def incoming():
    logger.info("received request. post data: {0}".format(request.get_data()))

    # every viber message is signed, you can verify the signature using this method
    if not viber.verify_signature(request.get_data(), request.headers.get('X-Viber-Content-Signature')):
        return Response(status=403)

    # this library supplies a simple way to receive a request object
    viber_request = viber.parse_request(request.get_data())

    if isinstance(viber_request, ViberMessageRequest):
        global selected_day  # exporting a global variable containg the day that we clicked

        sender_id = viber_request.sender.id
        message = viber_request.message.text

        if message.lower() == 'dates':
            viber.send_messages(sender_id, [
                TextMessage(text=dates_resp, keyboard=days_kb)
            ])
        elif message in movies_data or message.lower() == 'today' or message.lower() == 'tomorrow':
            # message here equals the date or today or tomorrow
            if message.lower() == 'today':
                selected_day = TODAY
            elif message.lower() == 'tomorrow':
                selected_day = days[1]
            else:
                selected_day = message
            reply = generate_movies_response(selected_day)
            kb = generate_movie_keyboard(selected_day)

            viber.send_messages(sender_id, [
                TextMessage(text=reply, keyboard=kb)
            ])
        elif message in movies_data[selected_day]:  # message here equals the name of the movie
            reply = gen_movie_resp(selected_day, message)
            poster = movies_data[selected_day][message]['poster_link']
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
    context = ('server.crt', 'server.key')
    app.run(port=8080)
