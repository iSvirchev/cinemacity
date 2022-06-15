import scrapy
import json
import datetime
import collections

from scrapy import Selector
from scrapy.http import TextResponse
from dateutil.relativedelta import relativedelta

CINEMA_ID = '1265'  # Бургас - Mall Galeria
API_URL = 'https://www.cinemacity.bg/bg/data-api-service/v1'

datetime_now = datetime.datetime.now()
url_date_format = "%Y-%m-%d"
# today_date = date.strftime(url_date_format)
next_year_date = (datetime_now + relativedelta(years=1)).strftime(url_date_format)
output_dates = {}


class MoviesSpider(scrapy.Spider):
    name = 'movies'
    start_urls = ['https://www.cinemacity.bg/']

    def parse(self, response):
        yield scrapy.Request('%s/quickbook/10106/dates/in-cinema/%s/until/%s?attr=&lang=en_GB' %
                             (API_URL, CINEMA_ID, next_year_date), callback=self.parse_dates)

    def parse_dates(self, response):
        resp_data = json.loads(response.text)
        dates = resp_data['body']['dates']

        dates.reverse()

        for date in dates:
            url = '%s/quickbook/10106/film-events/in-cinema/%s/at-date/%s?attr=&lang=en_GB' % (
                API_URL, CINEMA_ID, date)

            yield scrapy.Request(url, callback=self.parse_movies)

    def parse_movies(self, response):
        resp_data = json.loads(response.text)
        body = resp_data['body']
        all_movies = body['films']
        all_showings = body['events']
        movies = []
        date = None

        for movie in all_movies:
            movie_id = movie['id']
            poster_link = movie['posterLink']  # posters can end in -sm -md -lg depending on size - might need 'sm'
            movie_name = movie['name']
            movie_screenings = []
            for event in all_showings:
                event_datetime = datetime.datetime.strptime(event['eventDateTime'], '%Y-%m-%dT%H:%M:%S')
                if date is None:
                    date = event_datetime.strftime('%d %b')
                if event['filmId'] == movie_id:
                    movie_screenings.append(event_datetime.strftime('%H:%M'))
            movie = {
                # 'movie_id': movie_id,
                'movie_name': movie_name,
                'movie_screenings': movie_screenings,
                'poster_link': poster_link,
            }
            movies.append(movie)

        yield {date: {'movies': movies}}

