# view_users_fixed.py
import sqlite3
from pathlib import Path

db = Path("reminders.db")
if not db.exists():
    print("لم أجد reminders.db في المجلد الحالي.")
    raise SystemExit(1)

conn = sqlite3.connect(str(db))
cur = conn.cursor()
cur.execute("PRAGMA table_info(users);")
cols = [r[1] for r in cur.fetchall()]
print("أعمدة جدول users:", cols)

print("\nآخر 20 سجلًا في users (مرتبة بحسب rowid):")
cur.execute("""
 SELECT rowid, user_id, username, first_name, last_name, registered_at, started_at
 FROM users
 ORDER BY rowid DESC
 LIMIT 20
""")
rows = cur.fetchall()
if not rows:
    print("لا سجلات في users.")
else:
    for r in rows:
        print(r)
conn.close()
