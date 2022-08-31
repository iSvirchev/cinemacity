import sqlite3


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

    def fetch_user_date(self, user_id):
        with self.conn:
            self.cursor.execute("SELECT selected_date FROM users WHERE user_id=:user_id", {'user_id': user_id})
        return self.cursor.fetchone()[0]

    def fetch_user(self, user_id):
        with self.conn:
            self.cursor.execute("SELECT * FROM users WHERE user_id=:user_id", {'user_id': user_id})
        return self.cursor.fetchone()

    def set_today_4_all_users(self, selected_date):
        with self.conn:
            self.cursor.execute("UPDATE users SET selected_date=:selected_date", {'selected_date': selected_date})

    def fetch_all_subscribed(self):
        with self.conn:
            result = self.cursor.execute("SELECT user_id FROM users WHERE subscribed=1").fetchall()
            return_list = []
            for user in result:
                return_list.append(user[0])  # 0 is the index of the user_id, if we select * rows - we use indices to
                # access the other rows
        return return_list

    def fetch_cinemas(self):
        with self.conn:
            rows = self.cursor.execute("""SELECT cinema_id, cinema_name, cinema_image_url FROM cinemas""").fetchall()
            headers = self.cursor.description
        return convert_result_to_dict(rows, headers)

    def fetch_today_json(self, cinema_id):
        with self.conn:
            result = self.cursor.execute("""SELECT json FROM today WHERE cinema_id=:cinema_id""",
                                         {'cinema_id': cinema_id}).fetchone()
        return result[0]

    def fetch_yesterday_json(self, cinema_id):
        with self.conn:
            result = self.cursor.execute("""SELECT json FROM yesterday WHERE cinema_id=:cinema_id""",
                                         {'cinema_id': cinema_id}).fetchone()
        return result[0]

    def fetch_all_movies(self):
        with self.conn:
            rows = self.cursor.execute("""SELECT * FROM movies""").fetchall()
            headers = self.cursor.description
        return convert_result_to_dict(rows, headers)