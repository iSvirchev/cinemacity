import sqlite3
from utility.paths import DB_PATH


# headers is cursor.description:
# a tuple with tuples with all table headers - [0] element is the name of the table header
def convert_result_to_dict(rows, headers):
    items = {}
    for row in rows:
        row_id = row[0]
        info = {}
        for i in range(len(headers)):
            header_name = headers[i][0]
            info[header_name] = row[i]
        items[row_id] = info
    return items


class MoviesTable:
    MOVIE_ID = 0
    MOVIE_NAME = 1
    POSTER_LINK = 2
    LINK = 3


class CinemasTable:
    CINEMA_ID = 0
    CINEMA_NAME = 1
    IMAGE_URL = 2
    MOVIES_TODAY = 3
    MOVIES_YESTERDAY = 4
    DATES = 5
    LAST_UPDATE = 6
    BROADCASTED_TODAY = 7
    MOVIES_TO_BROADCAST = 8
    GROUP_ID = 9


class Events:
    EVENT_ID = 0
    CINEMA_ID = 1
    MOVIE_ID = 2
    DATE = 3
    EVENT_TIMES = 4


class UsersTable:
    USER_ID = 0
    USER_NAME = 1
    SUBSCRIBED = 2
    SELECTED_CINEMA_ID = 3
    SELECTED_DATE = 4


class DatabaseCommunication:
    # SQLite does not have a separate Boolean storage class.
    # Instead, Boolean values are stored as integers 0 (false) and 1 (true).
    def __init__(self):
        # self.conn = sqlite3.connect(':memory:', check_same_thread=False)  # runtime DB used for debugging
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.set_pragma_settings()
        self.create_config_table()
        self.create_users_table()
        self.create_movies_table()
        self.create_cinemas_table()

    def set_pragma_settings(self):
        # https://stackoverflow.com/a/27290180/15266844
        with self.conn:
            self.conn.execute("""PRAGMA journal_mode = WAL""")
            self.conn.execute("""PRAGMA synchronous = NORMAL""")

    ################################
    #        CREATE TABLES
    ################################
    def create_config_table(self):
        with self.conn:
            self.cursor.execute("""CREATE TABLE IF NOT EXISTS config (
                param TEXT UNIQUE,
                value TEXT
                );""")

    def create_users_table(self):
        with self.conn:
            self.cursor.execute("""CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                user_name TEXT,
                subscribed INTEGER DEFAULT TRUE,
                selected_cinema_id TEXT DEFAULT NULL,
                selected_date TEXT DEFAULT NULL
                )""")

    def create_cinemas_table(self):
        with self.conn:
            self.cursor.execute("""CREATE TABLE IF NOT EXISTS cinemas (
                cinema_id        TEXT PRIMARY KEY,
                cinema_name      TEXT,
                image_url        TEXT,
                movies_today     TEXT,
                movies_yesterday TEXT,
                dates            TEXT,
                last_update      TEXT,
                broadcasted_today INTEGER DEFAULT FALSE,
                movies_to_broadcast TEXT DEFAULT NULL,
                group_id         TEXT
            );""")

    def create_movies_table(self):
        with self.conn:
            self.cursor.execute("""CREATE TABLE IF NOT EXISTS movies (
                movie_id    TEXT PRIMARY KEY,
                movie_name  TEXT,
                poster_link TEXT,
                link        TEXT
            );""")

    def create_events_table(self):
        with self.conn:
            self.cursor.execute("""CREATE TABLE IF NOT EXISTS events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                cinema_id        TEXT,
                movie_id         TEXT,
                date TEXT,
                event_times TEXT,
                FOREIGN KEY (movie_id) REFERENCES movies (movie_id),
                FOREIGN KEY (cinema_id) REFERENCES cinemas (cinema_id)
                    );""")

    def delete_events_table(self):
        with self.conn:
            self.cursor.execute("""DROP TABLE IF EXISTS events""")

    ################################
    #        CONFIG QUERIES
    ################################
    def fetch_config_value(self, param):
        with self.conn:
            result = self.cursor.execute("SELECT value FROM config WHERE param=:param",
                                         {'param': param}).fetchone()[0]
        return result

    ################################
    #        USERS QUERIES
    ################################
    def add_user(self, user_id, user_name, selected_date):
        with self.conn:
            self.cursor.execute("""INSERT OR IGNORE INTO users(user_id, user_name, selected_date) 
                                VALUES (:user_id, :user_name, :selected_date)""",
                                {'user_id': user_id, 'user_name': user_name, 'selected_date': selected_date})

    def set_user_date(self, user_id, selected_date):
        with self.conn:
            self.cursor.execute("""UPDATE users 
                                SET selected_date=:selected_date 
                                WHERE user_id=:user_id""",
                                {'user_id': user_id, 'selected_date': selected_date})

    def set_user_cinema(self, user_id, cinema_id):
        with self.conn:
            self.cursor.execute("""UPDATE users 
                                SET selected_cinema_id=:cinema_id 
                                WHERE user_id=:user_id""",
                                {'user_id': user_id, 'cinema_id': cinema_id})

    def fetch_user(self, user_id):
        with self.conn:
            result = self.cursor.execute("SELECT * FROM users WHERE user_id=:user_id",
                                         {'user_id': user_id}).fetchone()
        return result

    # noinspection SqlWithoutWhere
    def set_today_4_all_users(self, selected_date):
        with self.conn:
            self.cursor.execute("UPDATE users SET selected_date=:selected_date", {'selected_date': selected_date})

    def update_user_subscription_status(self, user_id, subscribed):
        with self.conn:
            self.cursor.execute("""UPDATE users SET subscribed=:subscribed WHERE user_id=:user_id""",
                                {'subscribed': subscribed, 'user_id': user_id})

    def fetch_subscribed_to_cinema(self, cinema_id):
        with self.conn:
            result = self.cursor.execute(
                """SELECT * FROM users WHERE selected_cinema_id=:cinema_id and subscribed=1;""",
                {'cinema_id': cinema_id}).fetchall()
            return_list = []
            for user in result:
                return_list.append(user[0])
        return return_list

    ################################
    #        MOVIES QUERIES
    ################################
    def add_movie(self, movie_id, movie_name, poster_link, link):
        with self.conn:
            self.cursor.execute("""INSERT OR IGNORE INTO movies (movie_id, movie_name, poster_link, link)
                    VALUES (:movie_id, :movie_name, :poster_link, :link)""",
                                {'movie_id': movie_id, 'movie_name': movie_name, "poster_link": poster_link,
                                 "link": link})

    def fetch_all_movies_names(self):
        with self.conn:
            self.cursor.row_factory = lambda cursor, row: row[0]
            rows = self.cursor.execute("""SELECT movie_name FROM movies""").fetchall()
            self.cursor.row_factory = None
        return rows

    def fetch_movie_by_id(self, movie_id):
        with self.conn:
            result = self.cursor.execute("""SELECT * FROM movies WHERE movie_id=:movie_id""",
                                         {'movie_id': movie_id}).fetchone()
        return result

    def fetch_movie_by_name(self, movie_name):
        with self.conn:
            result = self.cursor.execute("""SELECT * FROM movies WHERE movie_name=:movie_name""",
                                         {'movie_name': movie_name}).fetchone()
        return result

    ################################
    #        CINEMAS QUERIES
    ################################
    def add_cinema(self, cinema_id, cinema_name, image_url, dates, group_id):
        with self.conn:
            self.cursor.execute("""INSERT OR IGNORE INTO cinemas(cinema_id, cinema_name, image_url, dates, group_id)
                        VALUES (:cinema_id, :cinema_name, :image_url, :dates, :group_id)""",
                                {'cinema_id': cinema_id, 'cinema_name': cinema_name, 'image_url': image_url,
                                 'dates': dates, 'group_id': group_id})

    def update_cinema_dates(self, cinema_id, dates):
        with self.conn:
            self.cursor.execute("""UPDATE cinemas SET dates=:dates WHERE cinema_id=:cinema_id""",
                                {'cinema_id': cinema_id, 'dates': dates})

    def update_cinema_broadcasted_today(self, cinema_id, broadcasted_today):
        with self.conn:
            self.cursor.execute(
                """UPDATE cinemas SET broadcasted_today=:broadcasted_today WHERE cinema_id=:cinema_id""",
                {'cinema_id': cinema_id, 'broadcasted_today': broadcasted_today})

    def fetch_movies_today(self, cinema_id):
        with self.conn:
            self.cursor.execute("""SELECT movies_today FROM cinemas WHERE cinema_id=:cinema_id""",
                                {'cinema_id': cinema_id})
            movie_ids_today = self.cursor.fetchone()[0]
        return movie_ids_today

    def update_movies_today(self, movie_ids, cinema_id, today):
        with self.conn:
            self.cursor.execute("""UPDATE cinemas SET movies_today=:movies_today, last_update=:last_update
                        WHERE cinema_id=:cinema_id""",
                                {'movies_today': movie_ids, 'cinema_id': cinema_id, 'last_update': today})

    def fetch_movies_yesterday(self, cinema_id):
        with self.conn:
            self.cursor.execute("""SELECT movies_yesterday FROM cinemas WHERE cinema_id=:cinema_id""",
                                {'cinema_id': cinema_id})
            movie_ids_yesterday = self.cursor.fetchone()[0]
        return movie_ids_yesterday

    def update_movies_yesterday(self, cinema_id):
        movie_ids_today = self.fetch_movies_today(cinema_id)
        with self.conn:
            self.cursor.execute("""UPDATE cinemas SET movies_yesterday=:movies_yesterday WHERE cinema_id=:cinema_id""",
                                {'cinema_id': cinema_id, 'movies_yesterday': movie_ids_today})

    def fetch_last_update(self, cinema_id):
        with self.conn:
            self.cursor.execute("""SELECT last_update FROM cinemas WHERE cinema_id=:cinema_id""",
                                {'cinema_id': cinema_id})
            last_update = self.cursor.fetchone()[0]
        return last_update

    def fetch_cinemas(self):
        with self.conn:
            rows = self.cursor.execute("""SELECT * FROM cinemas""").fetchall()
            headers = self.cursor.description
        return convert_result_to_dict(rows, headers)

    def update_movies_to_broadcast(self, cinema_id, m2b):
        with self.conn:
            self.cursor.execute(
                """UPDATE cinemas SET movies_to_broadcast=:movies_to_broadcast WHERE cinema_id=:cinema_id""",
                {'cinema_id': cinema_id, 'movies_to_broadcast': m2b})

    # def fetch_cinema_names(self):
    #     with self.conn:
    #         self.cursor.row_factory = lambda cursor, row: row[0]
    #         rows = self.cursor.execute("""SELECT cinema_name FROM cinemas""").fetchall()
    #         self.cursor.row_factory = None
    #     return rows

    def fetch_cinema_by_name(self, cinema_name):
        with self.conn:
            result = self.cursor.execute("""SELECT * FROM cinemas WHERE cinema_name=:cinema_name""",
                                         {'cinema_name': cinema_name}).fetchone()
        return result

    def fetch_cinema_by_id(self, cinema_id):
        with self.conn:
            result = self.cursor.execute("""SELECT * FROM cinemas WHERE cinema_id=:cinema_id""",
                                         {'cinema_id': cinema_id}).fetchone()
        return result

    def fetch_cinemas_by_groupId_not_broadcasted(self, group_id):
        with self.conn:
            rows = self.cursor.execute("""SELECT * FROM cinemas WHERE group_id=:group_id 
            AND broadcasted_today==FALSE""", {'group_id': group_id}).fetchall()
            headers = self.cursor.description
        return convert_result_to_dict(rows, headers)

    ################################
    #        EVENTS QUERIES
    ################################
    def add_event(self, cinema_id, movie_id, date, event_times):
        with self.conn:
            self.cursor.execute("""INSERT INTO events (cinema_id, movie_id, date, event_times) 
            VALUES (:cinema_id, :movie_id, :date, :event_times)""",
                                {'cinema_id': cinema_id, 'movie_id': movie_id, 'date': date,
                                 'event_times': event_times})

    def fetch_event_times(self, cinema_id, movie_id, date):
        with self.conn:
            result = self.cursor.execute(
                """SELECT e.event_times FROM events as e
                JOIN cinemas c on e.cinema_id = c.cinema_id
                JOIN movies m on e.movie_id = m.movie_id
                WHERE c.cinema_id=:cinema_id
                AND m.movie_id=:movie_id
                AND e.date=:date;""",
                {'cinema_id': cinema_id, 'movie_id': movie_id, 'date': date}).fetchone()
        return result

    def fetch_movies_in_cinema_by_date(self, cinema_id, date):
        with self.conn:
            rows = self.cursor.execute(
                """SELECT m.movie_name, m.poster_link, m.link
                FROM events as e
                JOIN cinemas c on e.cinema_id = c.cinema_id
                JOIN movies m on e.movie_id = m.movie_id
                WHERE c.cinema_id=:cinema_id
                AND e.date=:date;""",
                {'cinema_id': cinema_id, 'date': date}).fetchall()
            headers = self.cursor.description
        return convert_result_to_dict(rows, headers)


db = DatabaseCommunication()
