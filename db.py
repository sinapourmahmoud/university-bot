import sqlite3

DB_PATH='cinema.db'


conn=sqlite3.connect(DB_PATH)

cursor=conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    tg_id INTEGER PRIMARY KEY,
    student_id_card INTEGER,
    full_name TEXT,
    is_student INTEGER,
    linked_student_id INTEGER,
    payment_proof_file_id TEXT,
    status TEXT,
    ticket_code TEXT
)
""")


# Optional: reset auto-increment counter


# conn = sqlite3.connect(DB_PATH)
# cursor = conn.cursor()

# cursor.execute("SELECT tg_id, full_name, is_student, linked_student_id, payment_proof_file_id, status, ticket_code FROM users")
# users = cursor.fetchall()

conn.commit()
conn.close()
# print(users)

print("✅ Database and table created successfully!")

