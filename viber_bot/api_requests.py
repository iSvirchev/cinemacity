import datetime
import json

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
        # cinema_image_url = cinema['imageUrl']

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

            log.info("Will start extracting date info for cinema: %s", cinema_name)
            dates_dict = {'dates': {}}
            for date in sorted_dates:
                movies = pull_movies_for_date(cinema['id'], date)
                dates_dict['dates'][date] = movies
            log.info("All date info extracted for cinema: %s", cinema_name)
            log.info("=================================================")
            return_cinemas[cinema_id] = dates_dict
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
            movie_obj = {'poster_link': movie['posterLink'].replace('md', 'sm'), 'movie_name': movie['name'],
                         'movie_link': movie['link'], 'trailer_link': movie['videoLink']}
            return_movies[movie_id] = movie_obj
            all_events[movie_id] = {'movie_screenings': []}
        log.debug("Movies extracted!")
        log.debug("Will start extracting the movie_screenings for cinema '%s' for date '%s'", cinema_id, date)
        for event in showings:
            film_id = event['filmId']
            event_datetime = datetime.datetime.strptime(event['eventDateTime'], '%Y-%m-%dT%H:%M:%S')
            all_events[film_id]['movie_screenings'].append(event_datetime.strftime('%H:%M'))
        log.debug("Movie_screenings extracted!")
        for film_id in all_events:
            return_movies[film_id]['movie_screenings'] = all_events[film_id]['movie_screenings']
        return return_movies
    else:
        log.error("The request was not processed properly.")
        return None


initialize_cinemas()
cinemas_complete = pull_cinemas()
for cin in cinemas:
    cinemas_complete[cin['id']]['name'] = cin['displayName']
    cinemas_complete[cin['id']]['imageUrl'] = cin['imageUrl']
