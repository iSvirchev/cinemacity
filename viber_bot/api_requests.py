import datetime
import json
# import sqlite3
import os
import time
import requests
from dateutil.relativedelta import relativedelta

import logger
import paths
from queries import *

log = logger.get_logger()

log.info("=================================================")
log.info("            Starting API Requests...             ")
log.info("=================================================")
url_date_format = "%Y-%m-%d"
datetime_now = datetime.datetime.now()
next_year_date = (datetime_now + relativedelta(years=1)).strftime(url_date_format)  # used in API structure
today = datetime_now.strftime(url_date_format)
API_URL = 'https://www.cinemacity.bg/bg/data-api-service/v1'

USE_MOCKED_DATA = False


def initialize_cinemas():
    url = '%s/quickbook/10106/cinemas/with-event/until/%s?attr=&lang=en_GB' % (API_URL, next_year_date)
    rsp = requests.get(url)
    log.info("Response is %s for URL '%s'." % (rsp.status_code, url))
    if rsp.status_code == 200:
        json_response = json.loads(rsp.text)
        global cinemas
        cinemas = json_response['body']['cinemas']
        log.info("Cinemas has been initialized!")
    else:
        log.error("The request was not processed properly.")


def pull_cinemas():
    log.info("Will start requesting the available dates for each cinema...")
    return_cinemas = {}
    for cin in cinemas:
        cin_id = cin['id']
        cin_name = cin['displayName']
        img_url = cin['imageUrl']
        groupId = cin['groupId']

        # delete_cinema_dates_for_cinema_id()   # DB
        # add_cinema()   # DB
        url = '%s/quickbook/10106/dates/in-cinema/%s/until/%s?attr=&lang=en_GB' % (API_URL, cin_id, next_year_date)
        rsp = requests.get(url)
        log.info("Response is %s for URL '%s'." % (rsp.status_code, url))

        if rsp.status_code == 200:
            data = json.loads(rsp.text)
            timestamps = data['body']['dates']
            log.info("Timestamps for %s - '%s' are:" % (cin_id, cin_name))
            log.info(str(timestamps))
            # The response will sometimes return the dates scrambled
            # we take the timestamp strings and convert them to datetime objects
            dates_timestamps = [datetime.datetime.strptime(timestamp, "%Y-%m-%d") for timestamp in timestamps]
            # then we sort the datetime objects via list.sort()
            dates_timestamps.sort()
            # we convert the datetime objects back to strings
            sorted_dates = [datetime.datetime.strftime(date, "%Y-%m-%d") for date in dates_timestamps]
            log.info("The dates have been sorted! Sorted timestamps:")
            log.info(str(sorted_dates))

            log.info("Will start extracting dates info for cinema: '%s'", cin_name)
            dates_dict = {'dates': {}}
            movies_set = set()
            for date in sorted_dates:
                all_movies_for_cinema = pull_movies_for_date(cin['id'], date)
                log.debug("All the movies in cinema '%s' have been extracted.", cin_name)
                all_movies_for_cinema_as_list = list(all_movies_for_cinema)
                for mov in all_movies_for_cinema_as_list:
                    movies_set.add(mov)
                log.debug("All the movies in cinema '%s' have been added to the cinema's movie_set.", cin_name)
                formatted_date = datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%d %b')
                dates_dict['dates'][formatted_date] = all_movies_for_cinema
                # add_cinema_date()   # DB
            # update_movies_today()   # DB
            log.info("All date info extracted for cinema: %s", cin_name)
            log.info("-------------------------------------------------")
            return_cinemas[cin_id] = dates_dict
            return_cinemas[cin_id]['name'] = cin_name
            return_cinemas[cin_id]['imageUrl'] = img_url
            return_cinemas[cin_id]['groupId'] = groupId
        else:
            log.error("The request was not processed properly.")
    return return_cinemas


def pull_movies_for_date(cin_id, date):
    url = '%s/quickbook/10106/film-events/in-cinema/%s/at-date/%s?attr=&lang=en_GB' % (
        API_URL, cin_id, date)
    rsp = requests.get(url)
    log.info("Response is %s for URL '%s'." % (rsp.status_code, url))

    if rsp.status_code == 200:
        data = json.loads(rsp.text)
        movies_from_data = data['body']['films']
        showings = data['body']['events']
        return_movies = {}
        all_events = {}

        log.debug("Will start extracting the movies for cinema '%s' for date '%s'", cin_id, date)
        for mov in movies_from_data:
            mov_id = mov['id']
            mov_name = mov['name']
            p_link = mov['posterLink'].replace('md', 'sm')
            m_link = mov['link']
            # trailer_link = movie['videoLink']   # might need later - currently not used

            # add_movie()   # DB
            movie_obj = {'movie_name': mov_name, 'poster_link': p_link, 'movie_link': m_link}
            return_movies[mov_id] = movie_obj
            all_events[mov_id] = {'movie_screenings': []}
        log.debug("Movies extracted!")
        log.debug("Will start extracting the movie_screenings for cinema '%s' for date '%s'", cin_id, date)
        for event in showings:
            film_id = event['filmId']
            # booking_link = event['bookingLink']   # might need later - currently not used
            event_datetime = datetime.datetime.strptime(event['eventDateTime'], '%Y-%m-%dT%H:%M:%S')
            event_datetime_formatted = event_datetime.strftime('%H:%M')
            all_events[film_id]['movie_screenings'].append(event_datetime_formatted)

        log.debug("Movie_screenings extracted!")
        for film_id in all_events:
            all_event_times_arr = all_events[film_id]['movie_screenings']
            # add_event()   # DB query location
            return_movies[film_id]['movie_screenings'] = all_event_times_arr
        return return_movies
    else:
        log.error("The request was not processed properly.")
        return None


def start_api_calls():
    api_start_time = time.time()
    initialize_cinemas()
    data = pull_cinemas()
    api_end_time = time.time()
    log.info("API calls are DONE! Working time is: %ds", api_end_time - api_start_time)
    return data


log.info("=================================================")


def return_mocked_cinemas():
    mocked_path = paths.MISC_PATH + "mocked_cinemas.json"
    if os.path.exists(mocked_path):
        with open(mocked_path, "r") as openfile:
            mocked_data = json.load(openfile)
    else:
        log.info("mocked_cinemas.json does not exist - will create it with API call's information.")
        mocked_data = start_api_calls()

        with open(mocked_path, "w") as outfile:
            outfile.write(json.dumps(mocked_data))
    return mocked_data


if USE_MOCKED_DATA:
    log.info("Using mocked data from mocked_cinemas.json!")
    cinemas = return_mocked_cinemas()
else:
    log.info("Using live data from API calls...")
    cinemas = start_api_calls()
log.info("=================================================")

log.info("Starting DB operations...")
db_start_time = time.time()
db = DatabaseCommunication(paths.DB_PATH)
db.delete_events_table()
db.create_events_table()

pulled_movies = {}  # To avoid repetitive queries about the same movie - we keep them here

for cinema_id, cinema in cinemas.items():
    cinema_name = cinema['name']
    image_url = cinema['imageUrl']
    dates = cinema['dates']
    group_id = cinema['groupId']
    all_dates = ';'.join(dates)

    db_cinema = db.fetch_cinema_by_id(cinema_id)
    if db_cinema is None:
        db.add_cinema(cinema_id, cinema_name, image_url, all_dates, group_id)
        log.info("'%s' has been added to the database!", cinema_name)
    else:
        db.update_cinema_dates(cinema_id, all_dates)
        db.update_cinema_broadcasted_today(cinema_id, False)
        log.info("'%s''s dates have been updated in the database!" % cinema_name)

    movie_set = set()
    for date_stamp, movies in dates.items():
        for m in list(movies):
            movie_set.add(m)

        for movie_id, movie in movies.items():
            movie_name = movie['movie_name']
            poster_link = movie['poster_link']
            link = movie['movie_link']
            event_times = ';'.join(movie['movie_screenings'])

            db.add_movie(movie_id, movie_name, poster_link, link)
            db.add_event(cinema_id, movie_id, date_stamp, event_times)

    last_update = db.fetch_last_update(cinema_id)
    movie_ids = ';'.join(movie_set)
    if last_update is None:  # should happen only on the very first run
        log.info("Last update is 'None' will update cinemas.movies_today then cinemas.movies_yesterday")
        db.update_movies_today(movie_ids, cinema_id, today)
        db.update_movies_yesterday(cinema_id)
    elif last_update == today:  # we update only today's info
        log.info("Last update day is today will update cinemas.movies_today only")
        db.update_movies_today(movie_ids, cinema_id, today)
    else:  # we update movies_yesterday with movies_today then we update movies_today
        log.info("Last update day is NOT today will update cinemas.movies_yesterday then cinemas.movies_today")
        db.update_movies_yesterday(cinema_id)
        db.update_movies_today(movie_ids, cinema_id, today)

    broadcast_cinema = db.fetch_cinema_by_id(cinema_id)
    movies_today = broadcast_cinema[CinemasTable.MOVIES_TODAY].split(';')
    movies_yesterday = broadcast_cinema[CinemasTable.MOVIES_YESTERDAY].split(';')

    m_today_set = set(movies_today)
    m_yesterday_set = set(movies_yesterday)
    diff_set = m_today_set.difference(m_yesterday_set)
    broadcast_movies = []
    for m_id in diff_set:
        if m_id not in pulled_movies:
            log.info("'%s' has NOT been pulled from DB yet - will fetch it now." % m_id)
            m_name = db.fetch_movie_by_id(m_id)[MoviesTable.MOVIE_NAME]
            pulled_movies[m_id] = m_name
        else:
            log.info("'%s' was ALREADY pulled from DB." % m_id)
            m_name = pulled_movies[m_id]
        log.info("Name of '%s' is '%s'" % (m_id, m_name))
        broadcast_movies.append(m_name)
    db.update_movies_to_broadcast(cinema_id, ';'.join(broadcast_movies))

db_end_time = time.time()
log.info("DB operations are DONE! Working time is: %ds", db_end_time - db_start_time)
log.info("=================================================")
