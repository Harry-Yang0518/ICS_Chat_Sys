import os
import sqlite3

class UserDatabase:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.db")
        self.conn = sqlite3.connect(self.db_path)
        self.setup()

    def setup(self):
        with self.conn as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS users
                            (username text, password text)''')

    def create_user(self, username, passwd):
        with self.conn as conn:
            if not conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone():
                conn.execute('INSERT INTO users VALUES (?, ?)', (username, passwd))
                return True
            else:
                print('Username already exists')
                return False

    def get_password(self, username):
        with self.conn as conn:
            user = conn.execute("SELECT password FROM users WHERE username = ?", (username,)).fetchone()
            return user[0] if user else None

    def get_users(self):
        with self.conn as conn:
            return [user[0] for user in conn.execute("SELECT username FROM users").fetchall()]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()

if __name__ == '__main__':
    with UserDatabase() as db:
        print(db.get_password('admin'))
        print(db.get_users())
