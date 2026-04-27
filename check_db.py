import sqlite3

con = sqlite3.connect("instance/app.db")
rows = con.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
print(rows)