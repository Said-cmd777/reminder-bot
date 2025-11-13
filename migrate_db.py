
import sqlite3
from datetime import datetime

DB_PATH = "reminders.db"

def ensure_column_exists(conn, table, column, coltype="INTEGER"):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall()]
    if column not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")
        conn.commit()
        print(f"Added column {column} to {table}")

def ensure_users_table(conn):
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
      user_id INTEGER PRIMARY KEY,
      started_at TEXT
    );
    """)
    conn.commit()
    print("Ensured users table exists.")

def main():
    conn = sqlite3.connect(DB_PATH)
    ensure_users_table(conn)
    
    ensure_column_exists(conn, "homeworks", "target_user_id", "INTEGER")
    print("Migration completed at", datetime.now().isoformat())
    conn.close()

if __name__ == "__main__":
    main()
