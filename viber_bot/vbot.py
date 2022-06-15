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


def generate_movies_response(day):
    movies_resp = 'Movies currently in cinema for date %s:\n' % day
    for movie in movies_data[day]['movies']:
        movies_resp = movies_resp + '\n' + movie['movie_name']
    return movies_resp


info_resp = 'Please type one of the following commands to retrieve movie information:\n' \
            '*Today* - will display today\'s movies on screen\n' \
            '*Tomorrow* - will display tomorrow\'s movies on screen\n' \
            '*Dates* - will provide you with buttons of dates from which you can choose.'


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

        if message.lower() == 'dates':
            viber.send_messages(sender_id, [
                TextMessage(text=dates_resp, keyboard=days_kb)
            ])
        elif message in movies_data:
            reply = generate_movies_response(message)
            viber.send_messages(sender_id, [
                TextMessage(text=reply)
            ])
        elif message.lower() == 'today':
            reply = generate_movies_response(days[0])
            viber.send_messages(sender_id, [
                TextMessage(text=reply)
            ])
        elif message.lower() == 'tomorrow':
            reply = generate_movies_response(days[1])
            viber.send_messages(sender_id, [
                TextMessage(text=reply)
            ])
        elif message.lower() == 'info':
            viber.send_messages(sender_id, [
                TextMessage(text=info_resp)
            ])
    elif isinstance(viber_request, ViberSubscribedRequest):
        viber.send_messages(viber_request.user.id, [
            TextMessage(text='Hello %s! Thanks you for subscribing!\n'
                             'Type *INFO* for more information on the available commands.' % viber_request.user.name)
        ])
    elif isinstance(viber_request, ViberConversationStartedRequest):
        reply = 'Welcome %s!\n %s' % (viber_request.user.name, info_resp)
        viber.send_messages(viber_request.user.id, [
            TextMessage(text=reply)
        ])
    elif isinstance(viber_request, ViberFailedRequest):
        print("Failed!")

    return Response(status=200)


if __name__ == "__main__":
    context = ('server.crt', 'server.key')
    app.run(port='8080')
