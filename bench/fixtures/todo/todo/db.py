import sqlite3


def init(conn=None):
    conn = conn or sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, title TEXT)")
    conn.executemany("INSERT INTO tasks (title) VALUES (?)", [("buy milk",), ("write report",), ("call mom",)])
    return conn


def search(conn, term):
    return conn.execute("SELECT id, title FROM tasks WHERE title LIKE '%" + term + "%'").fetchall()
