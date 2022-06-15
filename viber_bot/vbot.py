from flask import Flask, request, Response
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages import *

# from viberbot.api.messages.keyboard_message import PictureMessage
import json

from viberbot.api.viber_requests import ViberConversationStartedRequest
from viberbot.api.viber_requests import ViberFailedRequest
from viberbot.api.viber_requests import ViberMessageRequest
from viberbot.api.viber_requests import ViberSubscribedRequest
from viberbot.api.viber_requests import ViberUnsubscribedRequest

app = Flask(__name__)
viber = Api(BotConfiguration(
    name='CinemaCity',
    avatar='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSzTmbvZUpF1ocKtWIZoV9jHPQ7dXqFi0UGnA&usqp=CAU',
    auth_token='4f56fc249e27e5cc-2f98f6f44db121e-587f215aa9e22f75'
))

JSON_FILE_PATH = open('..\\cinemacity_crawlers\\movies.json')
movies_data = json.load(JSON_FILE_PATH)
JSON_FILE_PATH.close()


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

movies_resp = 'Movies currently in cinema for date %s:\n' % days[0]
for movie in movies_data[days[0]]['movies']:
    movies_resp = movies_resp + '\n' + movie['movie_name']


def generate_keyboard(days_arr):
    keyboard = {
        "Type": "keyboard",
        "Buttons": []
    }

    button_tpl = {
        "Columns": 2,
        "Rows": 2,
        "BgColor": "#e6f5ff",
        "BgLoop": True,
        "ActionType": "reply",
        "ActionBody": "<add_action_body>",
        "Text": "<add_btn_txt>"
    }

    for day in days_arr:
        day_btn = button_tpl.copy()  # we use .copy() as a simple assignment operator '=' gives us object reference
        day_btn['ActionBody'] = day
        day_btn['Text'] = day
        keyboard['Buttons'].append(day_btn)

    return keyboard


days_kb = generate_keyboard(days)


@app.route('/', methods=['POST'])
def incoming():
    # every viber message is signed, you can verify the signature using this method
    if not viber.verify_signature(request.get_data(), request.headers.get('X-Viber-Content-Signature')):
        return Response(status=403)

    # this library supplies a simple way to receive a request object
    viber_request = viber.parse_request(request.get_data())

    if isinstance(viber_request,
                  ViberMessageRequest):  # check this https://developers.viber.com/docs/api/python-bot-api/#request-object
        sender_id = viber_request.sender.id
        message = viber_request.message.text
        print(message)
        print(movies_data)
        print(message in movies_data)
        if message.lower() == 'dates':
            viber.send_messages(sender_id, [
                TextMessage(text=dates_resp, keyboard=days_kb)
            ])
        elif message in movies_data:
            viber.send_messages(sender_id, [
                TextMessage(text=movies_resp)
            ])
    elif isinstance(viber_request, ViberSubscribedRequest):
        viber.send_messages(viber_request.user.id, [
            TextMessage(text='Hello %s. Thanks you for subscribing!' % viber_request.user.name)
        ])
    elif isinstance(viber_request, ViberConversationStartedRequest):
        print(viber_request.context)
        viber.send_messages(viber_request.user.id, [
            TextMessage(text='Welcome %s!' % viber_request.user.name)
        ])
    elif isinstance(viber_request, ViberFailedRequest):
        print()
        # logger.warn("client failed receiving message. failure: {0}".format(viber_request))

    return Response(status=200)


if __name__ == "__main__":
    context = ('server.crt', 'server.key')
    app.run(port='8080')
