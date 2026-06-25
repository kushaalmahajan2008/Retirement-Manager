import sqlite3
from config import database_file

def get_conn():
    conn=sqlite3.Connection(database_file)
    return conn