import datetime

from time import strftime
from flask import Flask, request, Response, render_template

from utility.database_comm import db, UsersTable, CinemasTable, MoviesTable
from utility.responses import Responses
from utility.logger import log
from utility.bot_config import viber_bot

from viberbot.api.messages import TextMessage, URLMessage
from viberbot.api.viber_requests import ViberConversationStartedRequest, ViberFailedRequest, ViberMessageRequest, \
    ViberSubscribedRequest

log.info("=================================================")
log.info("               Starting Viber Bot...             ")
log.info("=================================================")
datetime_now = datetime.datetime.now()
tomorrow_datetime = datetime_now + datetime.timedelta(days=1)
today = datetime_now.strftime('%d %b')
tomorrow = tomorrow_datetime.strftime('%d %b')
url_date_format = "%Y-%m-%d %H:%M:%S"
today_timestamp = strftime(url_date_format)
log.info('Today is: ' + today)
log.info('Tomorrow is: ' + tomorrow)

rsp = Responses()
db.set_today_4_all_users(today)
log.info('All users\' default dates have been set to today!')

app = Flask(__name__)

log.info("-------------------------------------------------")
cinemas = db.fetch_cinemas()
log.info("cinemas has been initialized.")

movie_names = db.fetch_all_movies_names()
log.info("movie_names has been initialized.")
cinema_names = set()
for cinema in cinemas.values():
    cinema_names.add(cinema['cinema_name'])
log.info("cinema_names has been initialized.")
log.info("=================================================")
log.info("              Viber Bot Started!                 ")
log.info("=================================================")


@app.route('/vbot', methods=['POST', 'GET'])
def incoming():
    if request.method == 'GET':
        log.debug("The method is GET")
        return Response(render_template('index.html'))

    request_data = request.get_data()
    log.debug("Received request! Post data: {0}".format(request_data))
    # Every viber message is signed, you can verify the signature using this method
    if not viber_bot.verify_signature(request_data, request.headers.get('X-Viber-Content-Signature')):
        return Response(status=403)

    viber_request = viber_bot.parse_request(request_data)

    if isinstance(viber_request, ViberMessageRequest):
        sender_name = viber_request.sender.name
        sender_id = viber_request.sender.id

        message = viber_request.message.text
        log.info("MSG received: '%s' from SENDER_ID: '%s' | SENDER_NAME: '%s'" % (message, sender_id, sender_name))
        db.add_user(sender_id, sender_name, today)

        user_db = db.fetch_user(sender_id)
        sender_sel_date = user_db[UsersTable.SELECTED_DATE]
        sender_sel_cinema_id = user_db[UsersTable.SELECTED_CINEMA_ID]
        # Pulling cinema data from cinemas object speeds up the bot, however a restart is required everyday

        # 1. First we check if the user already selected a cinema - if YES we extract the dates of the cinema
        if sender_sel_cinema_id is not None:
            sel_cinema_dates = cinemas[sender_sel_cinema_id]['dates'].split(';')
        # We want to keep the communication with the bot 'free' so that the user can switch choices at anytime
        # In the following order we check if wave received the following msgs from the user:
        # 1. subscribe/unsubscribe to our new movie newsletter
        if message.lower() == 'sub' or message.lower() == 'unsub':
            is_subscribed = user_db[UsersTable.SUBSCRIBED]
            sub_msg = 'An issue occurred...'
            if not is_subscribed and message.lower() == 'sub':
                db.update_user_subscription_status(sender_id, 1)
                sub_msg = rsp.sub_unsubbed
            elif not is_subscribed and message.lower() == 'unsub':
                sub_msg = rsp.unsub_unsubbed
            if is_subscribed and message.lower() == 'sub':
                sub_msg = rsp.sub_subbed
            if is_subscribed and message.lower() == 'unsub':
                db.update_user_subscription_status(sender_id, 0)
                sub_msg = rsp.unsub_subbed
            viber_bot.send_messages(sender_id, [TextMessage(text=sub_msg)])
        # 2. a name of a cinema name - if YES we assign the cinema to the user -> user_cinema_id
        elif message in cinema_names:
            user_cinema_id = db.fetch_cinema_by_name(message)[CinemasTable.CINEMA_ID]
            db.set_user_cinema(sender_id, user_cinema_id)
            viber_bot.send_messages(sender_id, [TextMessage(text=rsp.cinema(message))])
        # 3. 'cinema'/'cinemas' in order to change their selected cinema -> we respond with cinema's names keyboard
        elif message.lower() == 'cinema' or message.lower() == 'cinemas' or sender_sel_cinema_id is None:
            viber_bot.send_messages(sender_id, [TextMessage(text=rsp.pick_cinema, keyboard=rsp.cinemas_kb(cinemas))])
        # 4. 'dates' -> we respond with all the dates keyboard for user's selected cinemas
        elif message.lower() == 'dates':
            viber_bot.send_messages(sender_id, [TextMessage(text=rsp.dates(), keyboard=rsp.dates_kb(sel_cinema_dates))])
        # 5. 'today'/'tomorrow' or a date from dates keyboard -> we respond with the movies keyboard for selected date
        # and we assign the corresponding date to the user -> selected_date
        elif message in sel_cinema_dates or message.lower() == 'today' or message.lower() == 'tomorrow':
            # message here equals the date or today or tomorrow
            if message.lower() == 'today':
                sel_day = today
            elif message.lower() == 'tomorrow':
                sel_day = tomorrow
            else:
                sel_day = message

            db.set_user_date(sender_id, sel_day)
            log.info("SENDER_ID: '%s' has selected a new day: '%s'" % (sender_id, sel_day))
            try:
                movies_in_cin_for_date = db.fetch_movies_in_cinema_by_date(sender_sel_cinema_id, sel_day)
                cinema_name = cinemas[sender_sel_cinema_id]['cinema_name']
                reply = rsp.movies(sel_day, movies_in_cin_for_date, cinema_name)
                kb = rsp.movie_kb(movies_in_cin_for_date)
            except KeyError as ke:
                log.error("Error while displaying movies.")
                reply = "No movie screenings for the selected day: *%s*" % sel_day
                kb = None
                log.info(reply)
                log.error(ke)
            viber_bot.send_messages(sender_id, [TextMessage(text=reply, keyboard=kb)])
        # 6. a name of a movie -> we respond with a link to the movie for the selected date and cinema + all showings
        elif message in movie_names:  # message here equals the name of the movie
            log.info("SENDER_ID: '%s' selected movie '%s' for day '%s' for cinema '%s'" %
                     (sender_id, message, sender_sel_date, sender_sel_cinema_id))
            senders_movie = db.fetch_movie_by_name(message)
            movie_id = senders_movie[MoviesTable.MOVIE_ID]
            event_times = db.fetch_event_times(sender_sel_cinema_id, movie_id, sender_sel_date)
            screenings = ''
            if event_times is not None:
                screenings = event_times[0].split(';')
            cinema_name = cinemas[sender_sel_cinema_id]['cinema_name']
            base_movie_url = senders_movie[MoviesTable.LINK]
            sel_date_w_year = "%s  %s" % (sender_sel_date, datetime_now.strftime('%Y'))
            url_date = datetime.datetime.strptime(sel_date_w_year, '%d %b %Y').strftime('%Y-%m-%d')
            resp_url = rsp.resp_url(base_movie_url, sender_sel_cinema_id, url_date, movie_id)
            # We send two messages here - First one is an URLMessage to the movie in the selected cinema
            viber_bot.send_messages(sender_id, [URLMessage(media=resp_url)])
            # The second message is a TextMessage containing the screenings of the movie for the selected date
            viber_bot.send_messages(sender_id,
                                    [TextMessage(
                                        text=rsp.screenings(message, sender_sel_date, cinema_name, screenings))])
        else:
            viber_bot.send_messages(sender_id, [TextMessage(text=rsp.info)])

    # When a new user subscribes -> we send a greeting message.
    elif isinstance(viber_request, ViberSubscribedRequest):
        subs_msg = 'SUBSCRIBED' if db.fetch_user(viber_request.user.id)[
            UsersTable.SUBSCRIBED] else 'NOT SUBSCRIBED'
        user_id = viber_request.user.id
        log.info("User '%s' has now %s to the bot and to the newsletter" % (user_id, subs_msg))
        viber_bot.send_messages(user_id, [TextMessage(text=rsp.new_user(viber_request.user.name, subs_msg))])
    # When a new conversation is initiated with the bot by an user -> we offer
    elif isinstance(viber_request, ViberConversationStartedRequest):
        viber_bot.send_messages(viber_request.user.id, [TextMessage(text=rsp.conv_started(viber_request.user.name),
                                                                    keyboard=rsp.cinemas_kb(cinemas))])
    elif isinstance(viber_request, ViberFailedRequest):
        log.error("Viber Request has failed")

    return Response(status=200)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
