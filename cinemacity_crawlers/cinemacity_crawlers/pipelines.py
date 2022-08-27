# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import sqlite3
import json

cinemas = {}
cinemas_to_dump = {}


class CinemacityCrawlersPipeline:
    def __init__(self):
        self.conn = sqlite3.connect('../vbot.db')
        self.cursor = self.conn.cursor()
        self.create_tables()

    def __del__(self):
        self.fix_cinemas()
        for cinema_id in cinemas_to_dump:
            self.cursor.execute(
                "INSERT OR REPLACE INTO yesterday(cinema_id, json) VALUES (:cinema_id, "
                "(SELECT json FROM today WHERE cinema_id=:cinema_id))", {'cinema_id': cinema_id})
            self.cursor.execute(
                "INSERT OR REPLACE INTO today(cinema_id, json) VALUES (:cinema_id, :json)",
                {'cinema_id': cinema_id, 'json': json.dumps(cinemas_to_dump[cinema_id])})
        self.conn.commit()
        self.conn.close()

    def create_tables(self):
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS today (
                                        cinema_id TEXT PRIMARY KEY,
                                        json TEXT
                                        )""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS yesterday (
                                                cinema_id TEXT PRIMARY KEY,
                                                json TEXT
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

    def fix_cinemas(self):  # we need each cinema to hold a dictionary of dates not an array of dictionaries of dates
        for cinema_key in cinemas:
            fixed_dict = {}
            for date_obj in cinemas[cinema_key]:
                for date_key in date_obj:
                    date_dict = date_obj[date_key]
                    fixed_dict[date_key] = date_dict
            cinemas_to_dump[cinema_key] = fixed_dict
