# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from time import strftime

from itemadapter import ItemAdapter
import sqlite3
import json

cinemas = {}
cinemas_to_dump = {}

url_date_format = "%Y-%m-%d %H:%M:%S"
today_timestamp = strftime(url_date_format)
today = today_timestamp.split()[0]


def fix_cinemas():  # we need each cinema to hold a dictionary of dates not an array of dictionaries of dates
    for cinema_key in cinemas:
        fixed_dict = {}
        for date_obj in cinemas[cinema_key]:
            for date_key in date_obj:
                date_dict = date_obj[date_key]
                fixed_dict[date_key] = date_dict
        cinemas_to_dump[cinema_key] = fixed_dict


class CinemacityCrawlersPipeline:
    def __init__(self):
        self.conn = sqlite3.connect('../vbot.db')  # this path is probably invalid in UNIX
        self.cursor = self.conn.cursor()
        self.create_tables()

    def __del__(self):
        fix_cinemas()
        for cinema_id in cinemas_to_dump:
            last_update = str(self.select_today_jsons_last_update(cinema_id))

            if last_update is None:  # last_update is None - update both columns
                self.update_yesterday_json(cinema_id)
                self.update_today_json(cinema_id, today_timestamp)
            else:   # last_update is not None - check if the last update was today
                if last_update.startswith(today):  # last_update's day is today - update only today_json
                    self.update_today_json(cinema_id, today_timestamp)
                else:  # last_update's day has changed - update both columns
                    self.update_yesterday_json(cinema_id)
                    self.update_today_json(cinema_id, today_timestamp)

        self.conn.commit()
        self.conn.close()

    def create_tables(self):
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS cinemas (
                                cinema_id TEXT PRIMARY KEY,
                                cinema_name TEXT NOT NULL,
                                cinema_image_url TEXT NOT NULL,
                                broadcast_movies TEXT,
                                today_json TEXT,
                                yesterday_json TEXT,
                                today_json_last_update TEXT
                                )""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS movies(
                                movie_id TEXT PRIMARY KEY,
                                movie_name TEXT NOT NULL,
                                poster_link TEXT NOT NULL,
                                movie_link TEXT NOT NULL,
                                trailer_link TEXT
                                )""")

    def fetch_cinemas(self):
        res = self.cursor.execute("SELECT cinema_id FROM cinemas").fetchall()
        for cin in res:
            cinema = cin[0]
            cinemas[cinema] = []

    def process_item(self, item, spider):  # item is the cinema dictionary
        if not cinemas:  # we check of cinemas is empty if empty - pull the info from DB
            self.fetch_cinemas()
        for cinema_id in item:
            if cinema_id in cinemas:
                cinemas[cinema_id].append(item[cinema_id])  # we add all the dates for the specific cinema
        return item

    def select_today_jsons_last_update(self, cinema_id):
        self.cursor.execute("""SELECT today_json_last_update FROM cinemas WHERE cinema_id=:cinema_id;""",
                            {'cinema_id': cinema_id})
        return self.cursor.fetchone()[0]

    def update_today_jsons_last_update(self, cinema_id, timestamp):
        self.cursor.execute("""UPDATE cinemas SET today_json_last_update=:timestamp WHERE cinema_id=:cinema_id""",
                            {'cinema_id': cinema_id, 'timestamp': timestamp})

    def update_today_json(self, cinema_id, timestamp):
        self.update_today_jsons_last_update(cinema_id, timestamp)
        self.cursor.execute(
            """UPDATE cinemas SET today_json=:today_json, broadcast_movies=NULL WHERE cinema_id=:cinema_id""",
            {'cinema_id': cinema_id, 'today_json': json.dumps(cinemas_to_dump[cinema_id])})

    def update_yesterday_json(self, cinema_id):
        self.cursor.execute(
            """UPDATE cinemas SET yesterday_json=(SELECT today_json FROM cinemas WHERE cinema_id=:cinema_id) 
            WHERE cinema_id=:cinema_id;""", {'cinema_id': cinema_id})