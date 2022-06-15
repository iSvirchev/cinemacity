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

DAYS = []
dates_resp = 'Which day are you interested in?\n'
i = 1
for dict_obj in movies_data:
    for key in dict_obj:
        DAYS.append(key)
        dates_resp = dates_resp + '\n' + (str(i) + '. ' + key)
        i = i + 1
print(dates_resp.rstrip())

i = 1
movies_resp = 'Movies currently in cinema for date %s:\n' % DAYS[0]
for movie in movies_data[0][DAYS[0]]['movies']:
    movies_resp = movies_resp + '\n' + str(i) + '. ' + movie['movie_name']
    i = i + 1


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
        message = viber_request.message.text.lower()

        if message == 'dates':
            viber.send_messages(sender_id, [
                TextMessage(text=dates_resp)
            ])
        elif message == 'movies':
            viber.send_messages(sender_id, [
                TextMessage(text=movies_resp)
            ])
        else:
            # lets echo back
            viber.send_messages(sender_id, [
                viber_request.message
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
