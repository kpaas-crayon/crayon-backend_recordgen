import os
import pymysql
from pymysql.cursors import DictCursor

def get_conn():
    conn = pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "Annyeong12!"),
        database=os.getenv("DB_NAME", "records"),
        charset="utf8mb4",
        cursorclass=DictCursor
    )
    return conn
