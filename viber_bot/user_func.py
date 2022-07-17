import sqlite3


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

    def set_today_4_all(self, selected_date):
        with self.conn:
            self.cursor.execute("UPDATE users SET selected_date=:selected_date", {'selected_date': selected_date})

    def fetch_all_subscribed(self):
        with self.conn:
            self.cursor.execute("SELECT user_id FROM users WHERE subscribed=1")
        return self.cursor.fetchall()[0]
