# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import sqlite3
import json

items = {}


class CinemacityCrawlersPipeline:
    def __init__(self):
        self.conn = sqlite3.connect('spiders.db')
        self.cursor = self.conn.cursor()
        self.create_tables()

    def __del__(self):
        self.cursor.execute("INSERT OR REPLACE INTO yesterday(cinema_id, json) VALUES ((SELECT cinema_id FROM today), "
                            "(SELECT json FROM today));")
        self.cursor.execute("INSERT OR REPLACE INTO today(cinema_id, json) VALUES (:cinema_id, :json);",
                            {'cinema_id': 1265, 'json': json.dumps(items)})
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

    def process_item(self, item, spider):  # item is the date dictionary
        for k in item:
            items[k] = item[k]

        return item
