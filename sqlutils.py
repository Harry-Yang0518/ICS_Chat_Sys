import os.path
import sqlite3

# 设置数据库的基本目录和路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "users.db")

def sql_init():
    # 初始化数据库和表
    try:
        with sqlite3.connect(db_path) as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS users
                         (username text, password text)''')
            conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")

def create_user(username, passwd):
    # 创建新用户，如果用户已存在，则返回0
    p = 1
    try:
        with sqlite3.connect(db_path) as conn:
            c = conn.cursor()
            # 使用参数化查询来防止SQL注入
            t = c.execute("SELECT * FROM users WHERE username=?", (username,)).fetchall()
            if not t:
                c.execute('INSERT INTO users VALUES (?,?)', (username, passwd))
            else:
                print('Username already exists')
                p = 0
            conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        p = 0
    return p

def get_password(username):
    # 获取特定用户的密码，如果用户不存在，则返回None
    try:
        with sqlite3.connect(db_path) as conn:
            c = conn.cursor()
            # 使用参数化查询
            t = c.execute("SELECT * FROM users WHERE username=?", (username,)).fetchall()
            if t:
                return t[0][1]
            else:
                return None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None

def get_users():
    # 获取所有用户的列表
    try:
        with sqlite3.connect(db_path) as conn:
            c = conn.cursor()
            t = c.execute("SELECT username FROM users").fetchall()
            return [i[0] for i in t]
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []

if __name__ == '__main__':
    print(get_password('admin'))
    print(get_users())
