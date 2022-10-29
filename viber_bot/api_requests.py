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
    log.info("Response is %s for URL '%s'." % (rsp.status_code, API_URL))
    if rsp.status_code == 200:
        json_response = json.loads(rsp.text)
        global cinemas
        cinemas = json_response['body']['cinemas']
        log.info("Cinemas has been initialized!")
    else:
        log.error("The request was not processed properly.")


def pull_cinemas():
    log.info("Will start requesting the available dates for each cinema...")
    for cinema in cinemas:
        cinema_id = cinema['id']
        # cinema_name = cinema['displayName']
        # cinema_image_url = cinema['imageUrl']
        url = '%s/quickbook/10106/dates/in-cinema/%s/until/%s?attr=&lang=en_GB' % (API_URL, cinema_id, next_year_date)
        rsp = requests.get(url)
        log.info("Response is %s for URL '%s'." % (rsp.status_code, API_URL))

        if rsp.status_code == 200:
            data = json.loads(rsp.text)
            timestamps = data['body']['dates']
            dates = [datetime.datetime.strptime(timestamp, "%Y-%m-%d") for timestamp in timestamps]
            # then we sort the datetime objects via list.sort()
            dates.sort()
            # we convert the datetime objects back to strings
            sorted_dates = [datetime.datetime.strftime(date, "%Y-%m-%d") for date in dates]

            for date in sorted_dates:
                pull_date(cinema['id'], date)
        else:
            log.error("The request was not processed properly.")


def pull_date(cinema_id, date):
    url = '%s/quickbook/10106/film-events/in-cinema/%s/at-date/%s?attr=&lang=en_GB' % (
        API_URL, cinema_id, date)
    rsp = requests.get(url)
    log.info("Response is %s for URL '%s'." % (rsp.status_code, API_URL))

    if rsp.status_code == 200:
        data = json.loads(rsp.text)
        movies = data['body']['films']
        showings = data['body']['events']
        movie_screenings = []

        for movie in movies:
            movie_id = movie['id']
            poster_link = movie['posterLink'].replace('md', 'sm')  # posters can end in -sm -md -lg depending on size
            movie_name = movie['name']
            movie_link = movie['link']
            trailer_link = movie['videoLink']
        for event in showings:
            event_datetime = datetime.datetime.strptime(event['eventDateTime'], '%Y-%m-%dT%H:%M:%S')
            movie_screenings.append(event_datetime.strftime('%H:%M'))
    else:
        log.error("The request was not processed properly.")


initialize_cinemas()
log.info(cinemas)
print()
pull_cinemas()
