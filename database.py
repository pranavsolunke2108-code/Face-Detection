import sqlite3

conn = sqlite3.connect("users.db")

cursor = conn.cursor()

# -----------------------------------
# Users Table
# -----------------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    username TEXT UNIQUE NOT NULL,

    password TEXT NOT NULL,

    role TEXT NOT NULL
)
""")

# -----------------------------------
# Attendance Table
# -----------------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    username TEXT NOT NULL,

    date TEXT NOT NULL,

    time TEXT NOT NULL
)
""")

conn.commit()

print("Database and tables created successfully")

conn.close()