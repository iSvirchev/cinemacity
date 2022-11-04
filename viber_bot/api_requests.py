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
    for cinema in cinemas:
        cinema_id = cinema['id']
        cinema_name = cinema['displayName']
        image_url = cinema['imageUrl']

        # delete_cinema_dates_for_cinema_id()   # DB
        # add_cinema()   # DB
        url = '%s/quickbook/10106/dates/in-cinema/%s/until/%s?attr=&lang=en_GB' % (API_URL, cinema_id, next_year_date)
        rsp = requests.get(url)
        log.info("Response is %s for URL '%s'." % (rsp.status_code, url))

        if rsp.status_code == 200:
            data = json.loads(rsp.text)
            timestamps = data['body']['dates']
            log.info("Timestamps for %s - '%s' are:" % (cinema_id, cinema_name))
            log.info(str(timestamps))
            # The response will sometimes return the dates scrambled
            # we take the timestamp strings and convert them to datetime objects
            dates = [datetime.datetime.strptime(timestamp, "%Y-%m-%d") for timestamp in timestamps]
            # then we sort the datetime objects via list.sort()
            dates.sort()
            # we convert the datetime objects back to strings
            sorted_dates = [datetime.datetime.strftime(date, "%Y-%m-%d") for date in dates]
            log.info("The dates have been sorted! Sorted timestamps:")
            log.info(str(sorted_dates))

            log.info("Will start extracting dates info for cinema: '%s'", cinema_name)
            dates_dict = {'dates': {}}
            movie_set = set()
            for date in sorted_dates:
                all_movies_for_cinema = pull_movies_for_date(cinema['id'], date)
                log.debug("All the movies in cinema '%s' have been extracted.", cinema_name)
                all_movies_for_cinema_as_list = list(all_movies_for_cinema)
                for m in all_movies_for_cinema_as_list:
                    movie_set.add(m)
                log.debug("All the movies in cinema '%s' have been added to the cinema's movie_set.", cinema_name)
                formatted_date = datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%d %b')
                dates_dict['dates'][formatted_date] = all_movies_for_cinema
                # add_cinema_date()   # DB
            # update_movies_today()   # DB
            log.info("All date info extracted for cinema: %s", cinema_name)
            log.info("=================================================")
            return_cinemas[cinema_id] = dates_dict
            return_cinemas[cinema_id]['name'] = cinema_name
            return_cinemas[cinema_id]['imageUrl'] = image_url
        else:
            log.error("The request was not processed properly.")
    return return_cinemas


def pull_movies_for_date(cinema_id, date):
    url = '%s/quickbook/10106/film-events/in-cinema/%s/at-date/%s?attr=&lang=en_GB' % (
        API_URL, cinema_id, date)
    rsp = requests.get(url)
    log.info("Response is %s for URL '%s'." % (rsp.status_code, url))

    if rsp.status_code == 200:
        data = json.loads(rsp.text)
        movies = data['body']['films']
        showings = data['body']['events']
        return_movies = {}
        all_events = {}

        log.debug("Will start extracting the movies for cinema '%s' for date '%s'", cinema_id, date)
        for movie in movies:
            movie_id = movie['id']
            movie_name = movie['name']
            poster_link = movie['posterLink'].replace('md', 'sm')
            link = movie['link']
            # trailer_link = movie['videoLink']   # might need later - currently not used

            # add_movie()   # DB
            movie_obj = {'movie_name': movie_name, 'poster_link': poster_link, 'movie_link': link}
            return_movies[movie_id] = movie_obj
            all_events[movie_id] = {'movie_screenings': []}
        log.debug("Movies extracted!")
        log.debug("Will start extracting the movie_screenings for cinema '%s' for date '%s'", cinema_id, date)
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
    log.info("Using live data from API calls.")
    cinemas = start_api_calls()

db_start_time = time.time()
db = DatabaseCommunication(paths.DB_PATH)
db.delete_events_table()
db.create_events_table()

for cinema_id, cinema in cinemas.items():
    cinema_name = cinema['name']
    image_url = cinema['imageUrl']
    dates = cinema['dates']
    all_dates = ';'.join(dates)

    db_cinema = db.fetch_cinema_by_id(cinema_id)
    if db_cinema is None:
        db.add_cinema(cinema_id, cinema_name, image_url, all_dates)  # CHECK THIS - we need to update dates
        log.info("'%s' has been added to the database!", cinema_name)
    else:
        db.update_cinema_dates(cinema_id, all_dates)
        log.info("'%s''s dates have been updated in the database!")

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
    else:  # we update movies_yesterday with movies_today and then we update movies_today
        log.info("Last update day is NOT today will update cinemas.movies_yesterday then cinemas.movies_today")
        db.update_movies_yesterday(cinema_id)
        db.update_movies_today(movie_ids, cinema_id, today)

db_end_time = time.time()
log.info("DB operations are DONE! Working time is: %ds", db_end_time - db_start_time)
