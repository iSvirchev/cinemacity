import sqlite3

import scrapy
import json
import datetime

from dateutil.relativedelta import relativedelta

# CINEMA_ID = '1265'  # Бургас - Mall Galeria
API_URL = 'https://www.cinemacity.bg/bg/data-api-service/v1'

datetime_now = datetime.datetime.now()
url_date_format = "%Y-%m-%d"
# today_date = date.strftime(url_date_format)
next_year_date = (datetime_now + relativedelta(years=1)).strftime(url_date_format)
output_dates = {}
cinemas = {}


class MoviesSpider(scrapy.Spider):
    name = 'movies'
    start_urls = ['https://www.cinemacity.bg/']
    conn = sqlite3.connect('../vbot.db')  # this path is probably invalid in UNIX
    cursor = conn.cursor()

    def parse(self, response):
        yield scrapy.Request('%s/quickbook/10106/cinemas/with-event/until/%s?attr=&lang=en_GB' %
                             (API_URL, next_year_date), callback=self.parse_cinemas)

    def parse_cinemas(self, response):
        resp_data = json.loads(response.text)
        global cinemas
        cinemas = resp_data['body']['cinemas']

        for cinema in cinemas:
            cinema_id = cinema['id']
            cinema_name = cinema['displayName']
            cinema_image_url = cinema['imageUrl']
            self.cursor.execute("INSERT OR IGNORE INTO cinemas(cinema_id, cinema_name, cinema_image_url) "
                                "VALUES (:cinema_id, :cinema_name, :cinema_image_url)",
                                {'cinema_id': cinema_id,
                                 'cinema_name': cinema_name,
                                 'cinema_image_url': cinema_image_url})
            self.conn.commit()
            yield scrapy.Request('%s/quickbook/10106/dates/in-cinema/%s/until/%s?attr=&lang=en_GB' %
                                 (API_URL, cinema_id, next_year_date), callback=self.parse_dates)

    def parse_dates(self, response):
        resp_data = json.loads(response.text)
        dates = resp_data['body']['dates']

        dates.reverse()  # we need to reverse the list as the spider would write the data to .json from end->beginning

        for date in dates:
            for cinema in cinemas:
                url = '%s/quickbook/10106/film-events/in-cinema/%s/at-date/%s?attr=&lang=en_GB' % (
                    API_URL, cinema['id'], date)

                yield scrapy.Request(url, callback=self.parse_movies)

    def parse_movies(self, response):
        global date_dict, cinema_id
        resp_data = json.loads(response.text)
        body = resp_data['body']
        all_movies = body['films']
        all_showings = body['events']
        movies = {}
        date = None
        movies_names_in_db = list(map(lambda n: n[0], self.cursor.execute("SELECT movie_name FROM movies").fetchall()))
        for movie in all_movies:
            movie_id = movie['id']
            poster_link = movie['posterLink'].replace('md', 'sm')  # posters can end in -sm -md -lg depending on size
            movie_name = movie['name']
            movie_link = movie['link']
            trailer_link = movie['videoLink']

            movie_screenings = []
            cinema_id = ''

            for event in all_showings:
                cinema_id = event['cinemaId']
                booking_link = event['bookingLink']  # currently not in use - might need in future
                event_datetime = datetime.datetime.strptime(event['eventDateTime'], '%Y-%m-%dT%H:%M:%S')
                if date is None:
                    date = event_datetime.strftime('%d %b')
                if event['filmId'] == movie_id:
                    movie_screenings.append(event_datetime.strftime('%H:%M'))
                movie = {
                    'movie_name': movie_name,
                    'movie_screenings': movie_screenings,
                    # 'poster_link': poster_link,
                    # 'movie_link': movie_link,
                    'booking_link': booking_link,
                    # 'trailer_link': trailer_link,
                }

            # Sometimes CinemaCity would release a movie with one movie_name and later rename it
            # Which breaks my movie_name bot responses  - so I add this check to bypass that without many DB operations
            if movie_name not in movies_names_in_db:
                self.cursor.execute(
                    "INSERT OR REPLACE INTO movies(movie_id, movie_name, poster_link, movie_link, trailer_link) "
                    "VALUES (:movie_id, :movie_name, :poster_link, :movie_link, :trailer_link);", {
                        'movie_id': movie_id,
                        'movie_name': movie_name,
                        'poster_link': poster_link,
                        'movie_link': movie_link,
                        'trailer_link': trailer_link
                    })
            self.conn.commit()

            movies[movie_id] = movie
            date_dict = {date: movies}
        yield {cinema_id: date_dict}
