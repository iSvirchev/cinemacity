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
next_year_date = (datetime_now + relativedelta(years=1)).strftime(url_date_format)
API_URL = 'https://www.cinemacity.bg/bg/data-api-service/v1'
cinemas = {}


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

        # delete_cinema_dates_for_cinema_id()
        # add_cinema()
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
                log.info("All the movies in cinema '%s' have been extracted.", cinema_name)
                all_movies_for_cinema_as_list = list(all_movies_for_cinema)
                for m in all_movies_for_cinema_as_list:
                    movie_set.add(m)
                log.info("All the movies in cinema '%s' have been added to the cinema's movie_set.", cinema_name)
                formatted_date = datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%d %b')
                dates_dict['dates'][formatted_date] = all_movies_for_cinema
                # add_cinema_date()
            # update_movies_today()
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

            # add_movie()
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
            # add_event()
            return_movies[film_id]['movie_screenings'] = all_event_times_arr
        return return_movies
    else:
        log.error("The request was not processed properly.")
        return None


# api_start_time = time.time()
# initialize_cinemas()
# cinemas = pull_cinemas()
# api_end_time = time.time()
# log.info("API calls are DONE! Working time is: %d", api_end_time - api_start_time)

mocked_data = {}
if os.path.exists("sample.json"):
    with open("sample.json", "r") as openfile:
        mocked_data = json.load(openfile)
else:
    api_start_time = time.time()
    initialize_cinemas()
    cinemas = pull_cinemas()
    api_end_time = time.time()
    log.info("API calls are DONE! Working time is: %d", api_end_time - api_start_time)

    mocked_data = cinemas
    with open("sample.json", "w") as outfile:
        outfile.write(json.dumps(cinemas))

db_start_time = time.time()
# We empty cinema_dates for current cinema - we do not need data from multiple days

conn = sqlite3.connect('test.db', check_same_thread=False)
c = conn.cursor()


def delete_events():
    with conn:
        c.execute("""DELETE FROM events""")


def delete_cinema_dates_for_cinema_id(cinema_id):
    with conn:
        c.execute("""DELETE FROM cinema_dates WHERE cinema_id=:cinema_id""",
                  {"cinema_id": cinema_id})


def add_cinema(cinema_id, cinema_name, image_url):
    with conn:
        c.execute("""INSERT OR IGNORE INTO cinemas(cinema_id, cinema_name, image_url)
                    VALUES (:cinema_id, :cinema_name, :image_url)""",
                  {'cinema_id': cinema_id, 'cinema_name': cinema_name, 'image_url': image_url})


def add_cinema_date(date_stamp, cinema_id):
    with conn:
        c.execute("""INSERT INTO cinema_dates (date, cinema_id) VALUES (:date, :cinema_id)""",
                  {'date': date_stamp, 'cinema_id': cinema_id})


def add_movie(movie_id, movie_name, poster_link, link):
    with conn:
        c.execute("""INSERT OR IGNORE INTO movies (movie_id, movie_name, poster_link, link)
                VALUES (:movie_id, :movie_name, :poster_link, :link)""",
                  {'movie_id': movie_id, 'movie_name': movie_name, "poster_link": poster_link, "link": link})


def add_event(movie_id, cinema_id, date_stamp, event_times):
    with conn:
        c.execute("""INSERT INTO events (movie_id, cinema_id, date, event_times)
                VALUES (:movie_id, :cinema_id, :date, :event_times)""",
                  {'movie_id': movie_id, 'cinema_id': cinema_id, 'date': date_stamp, "event_times": event_times})


def update_movies_today(movie_ids, cinema_id):
    with conn:
        c.execute("""UPDATE cinemas SET movies_today=:movies_today
                    WHERE cinema_id=:cinema_id""",
                  {'movies_today': movie_ids, 'cinema_id': cinema_id})


delete_events()

for cinema_id, cinema in mocked_data.items():
    cinema_name = cinema['name']
    image_url = cinema['imageUrl']
    dates = cinema['dates']

    log.info("Dates for cinema '%s' have been deleted", cinema_name)
    delete_cinema_dates_for_cinema_id(cinema_id)
    add_cinema(cinema_id, cinema_name, image_url)
    log.info("'%s' has been added to the database!", cinema_name)

    movie_set = set()
    for date_stamp, movies in dates.items():
        add_cinema_date(date_stamp, cinema_id)
        log.info("Date '%s' added to the DB for cinema '%s'" % (date_stamp, cinema_name))
        for m in list(movies):
            movie_set.add(m)

        for movie_id, movie in movies.items():
            movie_name = movie['movie_name']
            poster_link = movie['poster_link']
            link = movie['movie_link']
            event_times = ';'.join(movie['movie_screenings'])

            add_movie(movie_id, movie_name, poster_link, link)
            add_event(movie_id, cinema_id, date_stamp, event_times)

    # TODO: We need to check the date here and move today_movies to yesterday_movies
    movie_ids = ';'.join(movie_set)
    update_movies_today(movie_ids, cinema_id)
    log.info("Today's movies have been updated for '%s'", cinema_name)
conn.commit()
conn.close()

db_end_time = time.time()
log.info("DB operations are DONE! Working time is: %d", db_end_time - db_start_time)
