# db.py
"""
DB helpers for Reminder bot — thread-safe approach:
- get_conn(db_path=None): returns a new sqlite3.Connection with WAL mode.
- ensure_tables(conn=None)
- insert_homework, get_homework, get_all_homeworks, delete_homework, mark_done, update_field
- register_user(conn, user_id, username, first_name, last_name, ts=None)
- update_user_display_name(conn, user_id, display_name)
- is_user_registered, get_all_registered_user_ids
"""

import os
import sqlite3
from typing import List, Optional

DEFAULT_DB_NAME = "reminders.db"

def get_conn(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Return a new sqlite3.Connection prepared for multi-thread use (check_same_thread=False)."""
    if db_path is None:
        db_path = os.path.join(os.path.dirname(__file__), DEFAULT_DB_NAME)
    conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        # Improve concurrency
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
    except Exception:
        # Some SQLite builds may not support changing PRAGMA — ignore if fails
        pass
    return conn

def ensure_tables(conn: Optional[sqlite3.Connection] = None):
    """Ensure required tables exist. If conn is None open a temporary one."""
    own = False
    if conn is None:
        conn = get_conn()
        own = True
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS homeworks (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      subject TEXT NOT NULL,
      description TEXT,
      due_at TEXT NOT NULL,
      pdf_type TEXT,
      pdf_value TEXT,
      conditions TEXT,
      created_by INTEGER,
      chat_id INTEGER,
      done INTEGER DEFAULT 0,
      reminders TEXT,
      target_user_id INTEGER,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
      -- keep schema tolerant: we create minimal set; many existing DBs may already differ
      user_id INTEGER UNIQUE NOT NULL,
      started_at TEXT,
      username TEXT,
      first_name TEXT,
      last_name TEXT,
      registered_at TEXT
    );
    """)
    # جدول لتتبع حالة "تم" لكل مستخدم لكل واجب
    cur.execute("""
    CREATE TABLE IF NOT EXISTS homework_completions (
      hw_id INTEGER NOT NULL,
      user_id INTEGER NOT NULL,
      completed_at TEXT DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (hw_id, user_id),
      FOREIGN KEY (hw_id) REFERENCES homeworks(id) ON DELETE CASCADE
    );
    """)
    # جدول للتذكيرات المخصصة للمستخدمين
    cur.execute("""
    CREATE TABLE IF NOT EXISTS custom_reminders (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      text TEXT NOT NULL,
      reminder_datetime TEXT NOT NULL,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)
    # جدول لتتبع حالة "تم" لكل تذكير مخصص
    cur.execute("""
    CREATE TABLE IF NOT EXISTS custom_reminder_completions (
      reminder_id INTEGER NOT NULL,
      user_id INTEGER NOT NULL,
      completed_at TEXT DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (reminder_id, user_id),
      FOREIGN KEY (reminder_id) REFERENCES custom_reminders(id) ON DELETE CASCADE
    );
    """)
    # جدول للحصص الأسبوعية
    cur.execute("""
    CREATE TABLE IF NOT EXISTS weekly_schedule_classes (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      group_number TEXT NOT NULL,
      day_name TEXT NOT NULL,
      time_start TEXT NOT NULL,
      time_end TEXT NOT NULL,
      course TEXT NOT NULL,
      location TEXT NOT NULL,
      class_type TEXT NOT NULL,
      is_alternating INTEGER DEFAULT 0,
      alternating_key TEXT,
      display_order INTEGER DEFAULT 0,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
      UNIQUE(group_number, day_name, time_start, course)
    );
    """)
    # جدول لمواقع الحجرات
    cur.execute("""
    CREATE TABLE IF NOT EXISTS schedule_locations (
      location_name TEXT PRIMARY KEY,
      maps_url TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    # جدول لتتبع الحصص الدورية (الأسبوع المرجعي)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS alternating_weeks_config (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      alternating_key TEXT UNIQUE NOT NULL,
      reference_date TEXT NOT NULL,
      description TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    # جدول إعدادات الإشعارات للمستخدمين
    cur.execute("""
    CREATE TABLE IF NOT EXISTS notification_settings (
      user_id INTEGER PRIMARY KEY,
      homework_reminders_enabled INTEGER DEFAULT 1,
      manual_reminders_enabled INTEGER DEFAULT 1,
      custom_reminders_enabled INTEGER DEFAULT 1,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)
    conn.commit()
    if own:
        conn.close()

# ---------------- Homeworks CRUD ----------------
def insert_homework(conn: sqlite3.Connection,
                    subject: str,
                    description: str,
                    due_at: str,
                    pdf_type: Optional[str],
                    pdf_value: Optional[str],
                    conditions: Optional[str],
                    created_by: int,
                    chat_id: int,
                    reminders: str,
                    target_user_id: Optional[int] = None) -> int:
    ensure_tables(conn)
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO homeworks
      (subject, description, due_at, pdf_type, pdf_value, conditions, created_by, chat_id, reminders, target_user_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (subject, description, due_at, pdf_type, pdf_value, conditions, created_by, chat_id, reminders, target_user_id))
    conn.commit()
    return cur.lastrowid

def get_homework(conn: sqlite3.Connection, hw_id: int):
    ensure_tables(conn)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM homeworks WHERE id = ?", (hw_id,))
    return cur.fetchone()

def get_all_homeworks(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    ensure_tables(conn)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM homeworks ORDER BY due_at")
    return cur.fetchall()

def delete_homework(conn: sqlite3.Connection, hw_id: int):
    ensure_tables(conn)
    cur = conn.cursor()
    cur.execute("DELETE FROM homeworks WHERE id = ?", (hw_id,))
    conn.commit()

def mark_done(conn: sqlite3.Connection, hw_id: int, user_id: int):
    """Mark homework as done for a specific user."""
    ensure_tables(conn)
    cur = conn.cursor()
    # إدراج أو تحديث في جدول homework_completions
    cur.execute("""
        INSERT OR REPLACE INTO homework_completions (hw_id, user_id, completed_at)
        VALUES (?, ?, datetime('now'))
    """, (hw_id, user_id))
    conn.commit()


def mark_undone(conn: sqlite3.Connection, hw_id: int, user_id: int):
    """Mark homework as not done for a specific user (undo done status)."""
    ensure_tables(conn)
    cur = conn.cursor()
    # حذف من جدول homework_completions
    cur.execute("DELETE FROM homework_completions WHERE hw_id = ? AND user_id = ?", (hw_id, user_id))
    conn.commit()


def is_homework_done_for_user(conn: sqlite3.Connection, hw_id: int, user_id: int) -> bool:
    """Check if homework is marked as done for a specific user."""
    ensure_tables(conn)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM homework_completions WHERE hw_id = ? AND user_id = ?", (hw_id, user_id))
    return cur.fetchone() is not None

def update_field(conn: sqlite3.Connection, hw_id: int, field: str, value):
    ensure_tables(conn)
    allowed = {"subject", "description", "due_at", "pdf_type", "pdf_value", "conditions", "reminders", "target_user_id"}
    if field not in allowed:
        raise ValueError("Field not allowed for update")
    cur = conn.cursor()
    if value is None:
        sql = f"UPDATE homeworks SET {field} = NULL WHERE id = ?"
        cur.execute(sql, (hw_id,))
    else:
        sql = f"UPDATE homeworks SET {field} = ? WHERE id = ?"
        cur.execute(sql, (value, hw_id))
    conn.commit()

# ---------------- Users helpers ----------------
def register_user(conn: sqlite3.Connection, user_id: int, username: Optional[str]=None,
                  first_name: Optional[str]=None, last_name: Optional[str]=None, ts: Optional[str]=None):
    """
    Robust upsert for users table:
    - Ensures required columns exist (adds them if missing).
    - Attempts UPDATE ... WHERE user_id = ?; if no rows updated, does INSERT.
    This avoids relying on 'id' column or ON CONFLICT which may not be supported on some DBs.
    """
    ensure_tables(conn)
    cur = conn.cursor()

    # 1) Inspect existing columns
    try:
        cur.execute("PRAGMA table_info(users)")
        pi = cur.fetchall()
        existing_cols = []
        for r in pi:
            if isinstance(r, sqlite3.Row) or isinstance(r, dict):
                existing_cols.append(r["name"])
            else:
                existing_cols.append(r[1])
    except Exception:
        existing_cols = []

    # 2) Add missing columns if needed (safe ALTER TABLE ADD COLUMN)
    expected = {
        "user_id": "INTEGER",
        "username": "TEXT",
        "first_name": "TEXT",
        "last_name": "TEXT",
        "registered_at": "TEXT",
        "started_at": "TEXT"
    }
    for col, col_type in expected.items():
        if col not in existing_cols:
            try:
                cur.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")
                conn.commit()
            except Exception:
                pass

    # 3) Try atomic UPDATE first (safer under race conditions)
    try:
        cur.execute("""
            UPDATE users
               SET username = ?, first_name = ?, last_name = ?, registered_at = ?
             WHERE user_id = ?
        """, (username, first_name, last_name, ts, user_id))
        if cur.rowcount == 0:
            # no row updated -> attempt insert
            try:
                cur.execute("""
                    INSERT INTO users (user_id, username, first_name, last_name, registered_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, username, first_name, last_name, ts))
            except sqlite3.IntegrityError:
                # possible race where another thread inserted simultaneously -> try update again
                cur.execute("""
                    UPDATE users
                       SET username = ?, first_name = ?, last_name = ?, registered_at = ?
                     WHERE user_id = ?
                """, (username, first_name, last_name, ts, user_id))
        conn.commit()
    except Exception:
        # Last-resort fallback: try INSERT OR REPLACE without relying on 'id' selection
        try:
            cur.execute("""
                INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, registered_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, username, first_name, last_name, ts))
            conn.commit()
        except Exception:
            raise

def update_user_display_name(conn: sqlite3.Connection, user_id: int, display_name: str):
    """
    Ensure 'display_name' column exists, then update the user's display name.
    Flexible parsing: accepts separators '_', ' ', '-', ','; splits on first occurrence.
    Left part -> last_name (لقب), right part -> first_name (اسم).
    If no separator -> store display_name and set first_name to the token (optional).
    """
    ensure_tables(conn)
    cur = conn.cursor()

    # Ensure display_name column exists
    try:
        cur.execute("PRAGMA table_info(users);")
        cols = [r[1] for r in cur.fetchall()]
    except Exception:
        cols = []

    if "display_name" not in cols:
        try:
            cur.execute("ALTER TABLE users ADD COLUMN display_name TEXT")
            conn.commit()
        except Exception:
            pass

    # Normalize and parse by first separator found
    s = (display_name or "").strip()
    lname = None
    fname = None
    separators = ["_", " ", "-", ","]
    sep_used = None
    for sep in separators:
        if sep in s:
            parts = s.split(sep, 1)
            sep_used = sep
            lname = parts[0].strip() or None
            fname = parts[1].strip() or None
            break

    if sep_used is None:
        # no separator found -> keep whole string as display_name,
        # and set first_name to the token (if reasonable)
        fname = s if s != "" else None

    # Attempt update then insert if needed
    try:
        cur.execute("""
            UPDATE users
               SET display_name = ?, first_name = COALESCE(?, first_name), last_name = COALESCE(?, last_name)
             WHERE user_id = ?
        """, (display_name, fname, lname, user_id))
        if cur.rowcount == 0:
            # insert new (username unknown here, set NULL)
            cur.execute("""
                INSERT INTO users (user_id, username, first_name, last_name, registered_at, display_name)
                VALUES (?, NULL, ?, ?, datetime('now'), ?)
            """, (user_id, fname, lname, display_name))
        conn.commit()
    except Exception:
        # fallback
        try:
            cur.execute("""
                INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, registered_at, display_name)
                VALUES (?, NULL, ?, ?, datetime('now'), ?)
            """, (user_id, fname, lname, display_name))
            conn.commit()
        except Exception:
            raise

def is_user_registered(conn: sqlite3.Connection, user_id: int) -> bool:
    ensure_tables(conn)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE user_id = ? LIMIT 1", (user_id,))
    return cur.fetchone() is not None

def get_all_registered_user_ids(conn: sqlite3.Connection) -> List[int]:
    ensure_tables(conn)
    cur = conn.cursor()
    # Use rowid order fallback if id missing
    try:
        cur.execute("SELECT user_id FROM users")
        rows = cur.fetchall()
        return [r[0] for r in rows]
    except Exception:
        return []

# ---------------- Custom Reminders CRUD ----------------
def insert_custom_reminder(conn: sqlite3.Connection, user_id: int, text: str, reminder_datetime: str) -> int:
    """Insert a custom reminder for a user."""
    ensure_tables(conn)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO custom_reminders (user_id, text, reminder_datetime)
        VALUES (?, ?, ?)
    """, (user_id, text, reminder_datetime))
    conn.commit()
    return cur.lastrowid


def get_custom_reminder(conn: sqlite3.Connection, reminder_id: int):
    """Get a custom reminder by ID."""
    ensure_tables(conn)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM custom_reminders WHERE id = ?", (reminder_id,))
    return cur.fetchone()


def get_all_custom_reminders_for_user(conn: sqlite3.Connection, user_id: int) -> List[sqlite3.Row]:
    """Get all custom reminders for a specific user."""
    ensure_tables(conn)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM custom_reminders WHERE user_id = ? ORDER BY reminder_datetime", (user_id,))
    return cur.fetchall()


def delete_custom_reminder(conn: sqlite3.Connection, reminder_id: int, user_id: int) -> bool:
    """Delete a custom reminder. Returns True if deleted, False if not found or not owned by user."""
    ensure_tables(conn)
    cur = conn.cursor()
    # Verify ownership before deleting
    cur.execute("SELECT id FROM custom_reminders WHERE id = ? AND user_id = ?", (reminder_id, user_id))
    if cur.fetchone() is None:
        return False
    cur.execute("DELETE FROM custom_reminders WHERE id = ? AND user_id = ?", (reminder_id, user_id))
    conn.commit()
    return True


def mark_custom_reminder_done(conn: sqlite3.Connection, reminder_id: int, user_id: int):
    """Mark a custom reminder as done for a user."""
    ensure_tables(conn)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO custom_reminder_completions (reminder_id, user_id, completed_at)
        VALUES (?, ?, datetime('now'))
    """, (reminder_id, user_id))
    conn.commit()


def mark_custom_reminder_undone(conn: sqlite3.Connection, reminder_id: int, user_id: int):
    """Mark a custom reminder as not done for a user."""
    ensure_tables(conn)
    cur = conn.cursor()
    cur.execute("DELETE FROM custom_reminder_completions WHERE reminder_id = ? AND user_id = ?", (reminder_id, user_id))
    conn.commit()


def is_custom_reminder_done_for_user(conn: sqlite3.Connection, reminder_id: int, user_id: int) -> bool:
    """Check if a custom reminder is marked as done for a user."""
    ensure_tables(conn)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM custom_reminder_completions WHERE reminder_id = ? AND user_id = ?", (reminder_id, user_id))
    return cur.fetchone() is not None

# ---------------- Notification Settings CRUD ----------------
def get_notification_settings(conn: sqlite3.Connection, user_id: int) -> Optional[sqlite3.Row]:
    """Get notification settings for a user. Returns None if not set (defaults to all enabled)."""
    ensure_tables(conn)
    # Ensure row_factory is set to Row for dictionary-like access
    if conn.row_factory is None:
        conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM notification_settings WHERE user_id = ?", (user_id,))
    return cur.fetchone()

def get_notification_setting(conn: sqlite3.Connection, user_id: int, setting_type: str) -> bool:
    """
    Get a specific notification setting for a user.
    setting_type: 'homework_reminders', 'manual_reminders', or 'custom_reminders'
    Returns True if enabled (default), False if disabled.
    """
    ensure_tables(conn)
    settings = get_notification_settings(conn, user_id)
    if not settings:
        return True  # Default: all enabled
    column_name = f"{setting_type}_enabled"
    try:
        return bool(settings[column_name])
    except (KeyError, TypeError):
        return True  # Default: enabled

def set_notification_setting(conn: sqlite3.Connection, user_id: int, setting_type: str, enabled: bool) -> bool:
    """
    Set a specific notification setting for a user.
    setting_type: 'homework_reminders', 'manual_reminders', or 'custom_reminders'
    enabled: True to enable, False to disable
    Returns True if successful.
    """
    ensure_tables(conn)
    cur = conn.cursor()
    column_name = f"{setting_type}_enabled"
    enabled_int = 1 if enabled else 0
    from datetime import datetime
    updated_at = datetime.now().isoformat()
    
    # Check if settings exist
    cur.execute("SELECT 1 FROM notification_settings WHERE user_id = ?", (user_id,))
    exists = cur.fetchone() is not None
    
    if exists:
        # Update existing settings
        cur.execute(f"UPDATE notification_settings SET {column_name} = ?, updated_at = ? WHERE user_id = ?",
                   (enabled_int, updated_at, user_id))
    else:
        # Create new settings with defaults, then update the specific setting
        cur.execute("""
            INSERT INTO notification_settings (user_id, homework_reminders_enabled, manual_reminders_enabled, 
                                              custom_reminders_enabled, updated_at)
            VALUES (?, 1, 1, 1, ?)
        """, (user_id, updated_at))
        # Now update the specific setting
        cur.execute(f"UPDATE notification_settings SET {column_name} = ?, updated_at = ? WHERE user_id = ?",
                   (enabled_int, updated_at, user_id))
    conn.commit()
    return True

def enable_all_notifications(conn: sqlite3.Connection, user_id: int) -> bool:
    """Enable all notifications for a user."""
    ensure_tables(conn)
    cur = conn.cursor()
    from datetime import datetime
    updated_at = datetime.now().isoformat()
    
    cur.execute("SELECT 1 FROM notification_settings WHERE user_id = ?", (user_id,))
    exists = cur.fetchone() is not None
    
    if exists:
        cur.execute("""
            UPDATE notification_settings 
            SET homework_reminders_enabled = 1, manual_reminders_enabled = 1, 
                custom_reminders_enabled = 1, updated_at = ?
            WHERE user_id = ?
        """, (updated_at, user_id))
    else:
        cur.execute("""
            INSERT INTO notification_settings (user_id, homework_reminders_enabled, manual_reminders_enabled, 
                                              custom_reminders_enabled, updated_at)
            VALUES (?, 1, 1, 1, ?)
        """, (user_id, updated_at))
    conn.commit()
    return True

def disable_all_notifications(conn: sqlite3.Connection, user_id: int) -> bool:
    """Disable all notifications for a user."""
    ensure_tables(conn)
    cur = conn.cursor()
    from datetime import datetime
    updated_at = datetime.now().isoformat()
    
    cur.execute("SELECT 1 FROM notification_settings WHERE user_id = ?", (user_id,))
    exists = cur.fetchone() is not None
    
    if exists:
        cur.execute("""
            UPDATE notification_settings 
            SET homework_reminders_enabled = 0, manual_reminders_enabled = 0, 
                custom_reminders_enabled = 0, updated_at = ?
            WHERE user_id = ?
        """, (updated_at, user_id))
    else:
        cur.execute("""
            INSERT INTO notification_settings (user_id, homework_reminders_enabled, manual_reminders_enabled, 
                                              custom_reminders_enabled, updated_at)
            VALUES (?, 0, 0, 0, ?)
        """, (user_id, updated_at))
    conn.commit()
    return True

# Quick init when run directly
if __name__ == "__main__":
    conn = get_conn()
    ensure_tables(conn)
    print("DB initialized at", os.path.join(os.path.dirname(__file__), DEFAULT_DB_NAME))
    conn.close()
