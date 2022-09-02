import sqlite3
import enum


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

# TODO: add enums for each table
class MoviesTable(enum.Enum):
    movie_id = 0
    movie_name = 1
    poster_link = 2
    movie_link = 3
    trailer_link = 4


class DatabaseCommunication:
    # SQLite does not have a separate Boolean storage class.
    # Instead, Boolean values are stored as integers 0 (false) and 1 (true).
    def __init__(self, db_path):
        # self.conn = sqlite3.connect(':memory:', check_same_thread=False)  # runtime DB used for debugging
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_users_table()

    def create_users_table(self):
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS users (
                                    user_id text primary key,
                                    user_name text,
                                    subscribed integer default true,
                                    selected_cinema_id text default null,
                                    selected_date text default null
                                    )""")

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
            self.cursor.execute("SELECT * FROM users WHERE user_id=:user_id", {'user_id': user_id})
        return self.cursor.fetchone()

    def set_today_4_all_users(self, selected_date):
        with self.conn:
            self.cursor.execute("UPDATE users SET selected_date=:selected_date", {'selected_date': selected_date})

    def update_user_subscription_status(self, user_id, subscribed):
        with self.conn:
            self.cursor.execute("""UPDATE users SET subscribed=:subscribed WHERE user_id=:user_id""",
                                {'subscribed': subscribed, 'user_id': user_id})

    def fetch_all_subscribed(self):
        with self.conn:
            result = self.cursor.execute("SELECT user_id FROM users WHERE subscribed=1").fetchall()
            return_list = []
            for user in result:
                return_list.append(user[0])  # 0 is the index of the user_id, if we select * rows - we use indices to
                # access the other rows
        return return_list

    def fetch_users_to_broadcast(self, cinema_id):
        with self.conn:
            result = self.cursor.execute(
                """SELECT * FROM users WHERE selected_cinema_id=:cinema_id and subscribed=1;""",
                {'cinema_id': cinema_id}).fetchall()
            return_list = []
            for user in result:
                return_list.append(user[0])
        return return_list

    def update_today_jsons(self, cinema_id, today_json):
        with self.conn:
            self.cursor.execute("""UPDATE cinemas SET today_json=:today_json WHERE cinema_id=:cinema_id""",
                                {'cinema_id': cinema_id, 'today_json': today_json})

    def fetch_movies(self):
        with self.conn:
            rows = self.cursor.execute("""SELECT * FROM movies""").fetchall()
            headers = self.cursor.description
        return convert_result_to_dict(rows, headers)

    def fetch_movies_names(self):
        with self.conn:
            self.cursor.row_factory = lambda cursor, row: row[0]
            rows = self.cursor.execute("""SELECT movie_name FROM movies""").fetchall()
            self.cursor.row_factory = None
        return rows

    def fetch_movie_by_id(self, movie_id, field_to_return):
        with self.conn:
            result = self.cursor.execute("""SELECT * FROM movies WHERE movie_id=:movie_id""",
                                         {'movie_id': movie_id}).fetchone()[field_to_return]
        print()
        return result  # TODO: check if we can use enum for table headers

    def fetch_movie_by_name(self, movie_name, field_to_return):
        with self.conn:
            result = self.cursor.execute("""SELECT * FROM movies WHERE movie_name=:movie_name""",
                                         {'movie_name': movie_name}).fetchone()[field_to_return]
        print()
        return result

    def fetch_cinemas(self):
        with self.conn:
            rows = self.cursor.execute("""SELECT * FROM cinemas""").fetchall()
            headers = self.cursor.description
        return convert_result_to_dict(rows, headers)

    def fetch_cinema_names(self):
        with self.conn:
            self.cursor.row_factory = lambda cursor, row: row[0]
            rows = self.cursor.execute("""SELECT cinema_name FROM cinemas""").fetchall()
            self.cursor.row_factory = None
        return rows

    def fetch_cinema_by_name(self, cinema_name, field_to_return):
        with self.conn:
            result = self.cursor.execute("""SELECT * FROM cinemas WHERE cinema_name=:cinema_name""",
                                         {'cinema_name': cinema_name}).fetchone()[field_to_return]
        print()
        return result

    def update_broadcast_movies(self, cinema_id, broadcast_movies):
        with self.conn:
            self.cursor.execute("""UPDATE cinemas SET broadcast_movies=:broadcast_movies WHERE cinema_id=:cinema_id""",
                                {'broadcast_movies': broadcast_movies, 'cinema_id': cinema_id})

    def fetch_broadcast_movies(self):
        with self.conn:
            result = self.cursor.execute("""SELECT * FROM cinemas""").fetchall()
            headers = self.cursor.description
        return convert_result_to_dict(result, headers)

# self.cursor.row_factory = lambda cursor, row: row[0]
# https://stackoverflow.com/a/23115247/15266844
# https://docs.python.org/3/library/sqlite3.html

# https://docs.python.org/3/library/sqlite3.html#sqlite3.Row
# def fetch_all_movies(self):
#     self.cursor.row_factory = sqlite3.Row
#     with self.conn:
#         row = self.cursor.execute("""SELECT * FROM movies""").fetchone()
#         headers = self.cursor.description
#         t = row.keys()
#         name = row['movie_name']
#         print()
#     return convert_result_to_dict(rows, headers)
