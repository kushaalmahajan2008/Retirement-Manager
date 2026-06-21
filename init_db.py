import sqlite3

mutual_fund_table="""CREATE TABLE IF NOT EXISTS MF_Transactions
(Id INTEGER PRIMARY KEY AUTOINCREMENT,
Date TEXT NOT NULL,
Transaction_Type TEXT NOT NULL,
Fund_Name TEXT NOT NULL,
Scheme_Code TEXT NOT NULL,
Units INTEGER NOT NULL,
Amount INTEGER NOT NULL)"""

with sqlite3.Connection("retirement_manager.db") as conn:
    conn.execute(mutual_fund_table)
    conn.commit()