"""SQLite database — stores users and their saved trip plans.
SQLite is a single file (trips.db), zero setup, perfect for this project size.
"""
import sqlite3
import json
from contextlib import contextmanager

DB_PATH = "trips.db"


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                destination TEXT NOT NULL,
                trip_data TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)


def create_user(email: str, hashed_password: str) -> int:
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO users (email, hashed_password) VALUES (?, ?)",
            (email, hashed_password),
        )
        return cur.lastrowid


def get_user_by_email(email: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


def save_trip(user_id: int, destination: str, trip_data: dict) -> int:
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO trips (user_id, destination, trip_data) VALUES (?, ?, ?)",
            (user_id, destination, json.dumps(trip_data)),
        )
        return cur.lastrowid


def get_user_trips(user_id: int) -> list:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, destination, created_at FROM trips WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_trip_by_id(trip_id: int, user_id: int):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM trips WHERE id = ? AND user_id = ?", (trip_id, user_id)
        ).fetchone()
        if not row:
            return None
        result = dict(row)
        result["trip_data"] = json.loads(result["trip_data"])
        return result
