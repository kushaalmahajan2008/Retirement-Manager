import sqlite3
from config import database_file

mutual_fund_table="""CREATE TABLE IF NOT EXISTS MF_Transactions
(Id INTEGER PRIMARY KEY AUTOINCREMENT,
Date TEXT NOT NULL,
Transaction_Type TEXT NOT NULL,
Fund_Name TEXT NOT NULL,
Scheme_Code TEXT NOT NULL,
Units REAL NOT NULL,
Amount REAL NOT NULL)"""

with sqlite3.Connection(database_file) as conn:
    conn.execute(mutual_fund_table)
    conn.commit()

mf_meta_table = """CREATE TABLE IF NOT EXISTS MF_Fund_Meta (
    Scheme_Code  TEXT PRIMARY KEY,
    ISIN         TEXT,
    Yahoo_Ticker TEXT,
    Fund_House   TEXT,
    Category     TEXT
)"""

with sqlite3.Connection("retirement_manager.db") as conn:
    conn.execute(mf_meta_table)
    conn.commit()