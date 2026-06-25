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