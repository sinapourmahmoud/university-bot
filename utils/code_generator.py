import sqlite3
from random import randint
DB_PATH='/data/cinema.db'


def generate_unique_code():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        while True:
            code = f"CINE-{randint(1,10000):05d}"
            cur.execute("SELECT 1 FROM users WHERE ticket_code=?", (code,))
            if not cur.fetchone():
                return code