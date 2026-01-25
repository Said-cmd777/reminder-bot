
"""
DB helpers for Reminder bot — thread-safe approach:
- get_conn(db_path=None): returns a database connection (SQLite or PostgreSQL)
- ensure_tables(conn=None)
- insert_homework, get_homework, get_all_homeworks, delete_homework, mark_done, update_field
- register_user(conn, user_id, username, first_name, last_name, ts=None)
- update_user_display_name(conn, user_id, display_name)
- is_user_registered, get_all_registered_user_ids
"""

import os
import sqlite3
from typing import List, Optional, Union
import logging

# Import database adapter
from db_adapter import get_conn as adapter_get_conn, close_conn
from db_config import DB_TYPE
from db_sql import get_create_table_sql, get_current_timestamp, get_returning_clause

logger = logging.getLogger(__name__)

DEFAULT_DB_NAME = "reminders.db"

def get_conn(db_path: Optional[str] = None):
    """
    Return a database connection (SQLite or PostgreSQL).
    
    Args:
        db_path: For SQLite only, override the default path
    
    Returns:
        Database connection
    """
    return adapter_get_conn(db_path)

def ensure_tables(conn=None):
    """Ensure required tables exist. If conn is None open a temporary one."""
    own = False
    if conn is None:
        conn = get_conn()
        own = True
    
    try:
        cur = conn.cursor()
        schemas = get_create_table_sql()
        
        # Create all tables
        for table_name, create_sql in schemas.items():
            try:
                cur.execute(create_sql)
                logger.debug(f"Table {table_name} created/verified")
            except Exception as e:
                logger.error(f"Error creating table {table_name}: {e}")
                raise
        
        conn.commit()
    finally:
        if own:
            close_conn(conn)


def insert_homework(conn,
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
    
    if DB_TYPE == "postgresql":
        # PostgreSQL uses %s placeholders and RETURNING clause
        cur.execute("""
        INSERT INTO homeworks
          (subject, description, due_at, pdf_type, pdf_value, conditions, created_by, chat_id, reminders, target_user_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """, (subject, description, due_at, pdf_type, pdf_value, conditions, created_by, chat_id, reminders, target_user_id))
        result = cur.fetchone()
        conn.commit()
        return result[0] if result else None
    else:
        # SQLite uses ? placeholders
        cur.execute("""
        INSERT INTO homeworks
          (subject, description, due_at, pdf_type, pdf_value, conditions, created_by, chat_id, reminders, target_user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (subject, description, due_at, pdf_type, pdf_value, conditions, created_by, chat_id, reminders, target_user_id))
        conn.commit()
        return cur.lastrowid

def get_homework(conn, hw_id: int):
    ensure_tables(conn)
    # Ensure row factory for dict-like access
    if DB_TYPE == "sqlite":
        conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    if DB_TYPE == "postgresql":
        # Import here to avoid circular dependency
        import psycopg2.extras
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM homeworks WHERE id = %s", (hw_id,))
        result = cur.fetchone()
        if result:
            from db_adapter import Row
            return Row(dict(result))
        return None
    else:
        cur.execute("SELECT * FROM homeworks WHERE id = ?", (hw_id,))
        return cur.fetchone()

def get_all_homeworks(conn) -> List:
    ensure_tables(conn)
    # Ensure row factory for dict-like access
    if DB_TYPE == "sqlite":
        conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    if DB_TYPE == "postgresql":
        import psycopg2.extras
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM homeworks ORDER BY due_at")
        results = cur.fetchall()
        from db_adapter import Row
        return [Row(dict(r)) for r in results]
    else:
        cur.execute("SELECT * FROM homeworks ORDER BY due_at")
        return cur.fetchall()

def delete_homework(conn, hw_id: int):
    ensure_tables(conn)
    cur = conn.cursor()
    if DB_TYPE == "postgresql":
        cur.execute("DELETE FROM homeworks WHERE id = %s", (hw_id,))
    else:
        cur.execute("DELETE FROM homeworks WHERE id = ?", (hw_id,))
    conn.commit()

def mark_done(conn, hw_id: int, user_id: int):
    """Mark homework as done for a specific user."""
    ensure_tables(conn)
    cur = conn.cursor()
    
    if DB_TYPE == "postgresql":
        cur.execute("""
            INSERT INTO homework_completions (hw_id, user_id, completed_at)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (hw_id, user_id) DO UPDATE SET completed_at = CURRENT_TIMESTAMP
        """, (hw_id, user_id))
    else:
        cur.execute("""
            INSERT OR REPLACE INTO homework_completions (hw_id, user_id, completed_at)
            VALUES (?, ?, datetime('now'))
        """, (hw_id, user_id))
    conn.commit()


def mark_undone(conn, hw_id: int, user_id: int):
    """Mark homework as not done for a specific user (undo done status)."""
    ensure_tables(conn)
    cur = conn.cursor()
    
    if DB_TYPE == "postgresql":
        cur.execute("DELETE FROM homework_completions WHERE hw_id = %s AND user_id = %s", (hw_id, user_id))
    else:
        cur.execute("DELETE FROM homework_completions WHERE hw_id = ? AND user_id = ?", (hw_id, user_id))
    conn.commit()


def is_homework_done_for_user(conn, hw_id: int, user_id: int) -> bool:
    """Check if homework is marked as done for a specific user."""
    ensure_tables(conn)
    cur = conn.cursor()
    if DB_TYPE == "postgresql":
        cur.execute("SELECT 1 FROM homework_completions WHERE hw_id = %s AND user_id = %s", (hw_id, user_id))
    else:
        cur.execute("SELECT 1 FROM homework_completions WHERE hw_id = ? AND user_id = ?", (hw_id, user_id))
    return cur.fetchone() is not None

def update_field(conn, hw_id: int, field: str, value):
    ensure_tables(conn)
    allowed = {"subject", "description", "due_at", "pdf_type", "pdf_value", "conditions", "reminders", "target_user_id"}
    if field not in allowed:
        raise ValueError("Field not allowed for update")
    cur = conn.cursor()
    
    placeholder = "%s" if DB_TYPE == "postgresql" else "?"
    
    if value is None:
        sql = f"UPDATE homeworks SET {field} = NULL WHERE id = {placeholder}"
        cur.execute(sql, (hw_id,))
    else:
        sql = f"UPDATE homeworks SET {field} = {placeholder} WHERE id = {placeholder}"
        cur.execute(sql, (value, hw_id))
    conn.commit()


def register_user(conn, user_id: int, username: Optional[str]=None,
                  first_name: Optional[str]=None, last_name: Optional[str]=None, ts: Optional[str]=None):
    """
    Robust upsert for users table:
    - Ensures required columns exist (adds them if missing - SQLite only).
    - Attempts UPDATE ... WHERE user_id = ?; if no rows updated, does INSERT.
    This avoids relying on 'id' column or ON CONFLICT which may not be supported on some DBs.
    """
    ensure_tables(conn)
    cur = conn.cursor()

    # For SQLite, check and add columns if needed
    if DB_TYPE == "sqlite":
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

        # Add missing columns for SQLite
        expected = {
            "user_id": "INTEGER",
            "username": "TEXT",
            "first_name": "TEXT",
            "last_name": "TEXT",
            "registered_at": "TEXT",
            "started_at": "TEXT",
            "display_name": "TEXT",
            "group_number": "TEXT"
        }
        for col, col_type in expected.items():
            if col not in existing_cols:
                try:
                    cur.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")
                    conn.commit()
                except Exception:
                    pass

    # Common upsert logic
    placeholder = "%s" if DB_TYPE == "postgresql" else "?"
    
    try:
        if DB_TYPE == "postgresql":
            # PostgreSQL: Use ON CONFLICT
            cur.execute("""
                INSERT INTO users (user_id, username, first_name, last_name, registered_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    registered_at = EXCLUDED.registered_at
            """, (user_id, username, first_name, last_name, ts))
        else:
            # SQLite: Try UPDATE then INSERT
            cur.execute(f"""
                UPDATE users
                   SET username = ?, first_name = ?, last_name = ?, registered_at = ?
                 WHERE user_id = ?
            """, (username, first_name, last_name, ts, user_id))
            if cur.rowcount == 0:
                try:
                    cur.execute("""
                        INSERT INTO users (user_id, username, first_name, last_name, registered_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (user_id, username, first_name, last_name, ts))
                except sqlite3.IntegrityError:
                    # Race condition - someone inserted it
                    cur.execute("""
                        UPDATE users
                           SET username = ?, first_name = ?, last_name = ?, registered_at = ?
                         WHERE user_id = ?
                    """, (username, first_name, last_name, ts, user_id))
        conn.commit()
    except Exception as e:
        logger.error(f"Error in register_user: {e}")
        # Final fallback for SQLite
        if DB_TYPE == "sqlite":
            try:
                cur.execute("""
                    INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, registered_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, username, first_name, last_name, ts))
                conn.commit()
            except Exception:
                raise
        else:
            raise

def update_user_display_name(conn, user_id: int, display_name: str, group_number: Optional[str] = None):
    """
    Ensure 'display_name' column exists, then update the user's display name.
    Flexible parsing: accepts separators '_', ' ', '-', ','; splits on first occurrence.
    Left part -> last_name (لقب), right part -> first_name (اسم).
    If no separator -> store display_name and set first_name to the token (optional).
    """
    ensure_tables(conn)
    cur = conn.cursor()

    # For SQLite, check and add columns if needed
    if DB_TYPE == "sqlite":
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
        if "group_number" not in cols:
            try:
                cur.execute("ALTER TABLE users ADD COLUMN group_number TEXT")
                conn.commit()
            except Exception:
                pass

    # Parse display name
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
        fname = s if s != "" else None

    # Update or insert
    placeholder = "%s" if DB_TYPE == "postgresql" else "?"
    current_ts = get_current_timestamp()
    
    try:
        if DB_TYPE == "postgresql":
            # PostgreSQL: Use ON CONFLICT
            if group_number is not None:
                cur.execute(f"""
                    INSERT INTO users (user_id, username, first_name, last_name, registered_at, display_name, group_number)
                    VALUES (%s, NULL, %s, %s, {current_ts}, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        display_name = EXCLUDED.display_name,
                        first_name = COALESCE(EXCLUDED.first_name, users.first_name),
                        last_name = COALESCE(EXCLUDED.last_name, users.last_name),
                        group_number = EXCLUDED.group_number
                """, (user_id, fname, lname, display_name, group_number))
            else:
                cur.execute(f"""
                    INSERT INTO users (user_id, username, first_name, last_name, registered_at, display_name)
                    VALUES (%s, NULL, %s, %s, {current_ts}, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        display_name = EXCLUDED.display_name,
                        first_name = COALESCE(EXCLUDED.first_name, users.first_name),
                        last_name = COALESCE(EXCLUDED.last_name, users.last_name)
                """, (user_id, fname, lname, display_name))
        else:
            # SQLite: Try UPDATE then INSERT
            if group_number is not None:
                cur.execute("""
                    UPDATE users
                       SET display_name = ?, first_name = COALESCE(?, first_name), last_name = COALESCE(?, last_name),
                           group_number = ?
                     WHERE user_id = ?
                """, (display_name, fname, lname, group_number, user_id))
            else:
                cur.execute("""
                    UPDATE users
                       SET display_name = ?, first_name = COALESCE(?, first_name), last_name = COALESCE(?, last_name)
                     WHERE user_id = ?
                """, (display_name, fname, lname, user_id))
            
            if cur.rowcount == 0:
                # No existing row, insert new one
                if group_number is not None:
                    cur.execute(f"""
                        INSERT INTO users (user_id, username, first_name, last_name, registered_at, display_name, group_number)
                        VALUES (?, NULL, ?, ?, {current_ts}, ?, ?)
                    """, (user_id, fname, lname, display_name, group_number))
                else:
                    cur.execute(f"""
                        INSERT INTO users (user_id, username, first_name, last_name, registered_at, display_name)
                        VALUES (?, NULL, ?, ?, {current_ts}, ?)
                    """, (user_id, fname, lname, display_name))
        conn.commit()
    except Exception as e:
        logger.error(f"Error in update_user_display_name: {e}")
        # Fallback for SQLite
        if DB_TYPE == "sqlite":
            try:
                if group_number is not None:
                    cur.execute(f"""
                        INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, registered_at, display_name, group_number)
                        VALUES (?, NULL, ?, ?, {current_ts}, ?, ?)
                    """, (user_id, fname, lname, display_name, group_number))
                else:
                    cur.execute(f"""
                        INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, registered_at, display_name)
                        VALUES (?, NULL, ?, ?, {current_ts}, ?)
                    """, (user_id, fname, lname, display_name))
                conn.commit()
            except Exception:
                raise
        else:
            raise


def get_user_display_info(conn, user_id: int) -> Optional:
    """Get display name and group number for a user."""
    ensure_tables(conn)
    cur = conn.cursor()
    placeholder = "%s" if DB_TYPE == "postgresql" else "?"
    
    try:
        if DB_TYPE == "postgresql":
            import psycopg2.extras
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(f"SELECT display_name, group_number FROM users WHERE user_id = {placeholder} LIMIT 1", (user_id,))
            result = cur.fetchone()
            if result:
                from db_adapter import Row
                return Row(dict(result))
            return None
        else:
            previous_factory = conn.row_factory
            conn.row_factory = sqlite3.Row
            cur.execute(f"SELECT display_name, group_number FROM users WHERE user_id = {placeholder} LIMIT 1", (user_id,))
            result = cur.fetchone()
            conn.row_factory = previous_factory
            return result
    except Exception as e:
        logger.error(f"Error in get_user_display_info: {e}")
        return None

def is_user_registered(conn, user_id: int) -> bool:
    ensure_tables(conn)
    cur = conn.cursor()
    placeholder = "%s" if DB_TYPE == "postgresql" else "?"
    cur.execute(f"SELECT 1 FROM users WHERE user_id = {placeholder} LIMIT 1", (user_id,))
    return cur.fetchone() is not None

def is_user_registration_complete(conn, user_id: int) -> bool:
    """Check if user has completed required registration fields."""
    ensure_tables(conn)
    cur = conn.cursor()
    placeholder = "%s" if DB_TYPE == "postgresql" else "?"
    
    # For SQLite, check column existence
    if DB_TYPE == "sqlite":
        try:
            cur.execute("PRAGMA table_info(users);")
            cols = [r[1] for r in cur.fetchall()]
        except Exception:
            cols = []
        if "display_name" not in cols or "group_number" not in cols:
            return False
    
    try:
        cur.execute(f"SELECT display_name, group_number FROM users WHERE user_id = {placeholder} LIMIT 1", (user_id,))
        row = cur.fetchone()
    except Exception:
        return False
    if not row:
        return False
    display_name = row[0]
    group_number = row[1]
    return len(str(display_name or "").strip()) > 0 and len(str(group_number or "").strip()) > 0

def get_all_registered_user_ids(conn) -> List[int]:
    ensure_tables(conn)
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT user_id FROM users")
        rows = cur.fetchall()
        return [r[0] for r in rows]
    except Exception:
        return []


def get_all_registered_users(conn) -> List[dict]:
    """
    Get all registered users with their full name and user_id.
    
    Returns:
        List of dicts with keys: user_id, display_name, first_name, last_name
    """
    ensure_tables(conn)
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT user_id, display_name, first_name, last_name FROM users ORDER BY user_id")
        rows = cur.fetchall()
        result = []
        for row in rows:
            user_id = row[0]
            display_name = row[1]
            first_name = row[2]
            last_name = row[3]
            
            # Build the full name from available data
            if display_name:
                full_name = display_name
            elif first_name or last_name:
                full_name = f"{first_name or ''} {last_name or ''}".strip()
            else:
                full_name = None
            
            result.append({
                'user_id': user_id,
                'full_name': full_name
            })
        return result
    except Exception:
        logger.exception("Error getting all registered users")
        return []


def insert_custom_reminder(conn, user_id: int, text: str, reminder_datetime: str) -> int:
    """Insert a custom reminder for a user."""
    ensure_tables(conn)
    cur = conn.cursor()
    
    if DB_TYPE == "postgresql":
        cur.execute("""
            INSERT INTO custom_reminders (user_id, text, reminder_datetime)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (user_id, text, reminder_datetime))
        result = cur.fetchone()
        conn.commit()
        return result[0] if result else None
    else:
        cur.execute("""
            INSERT INTO custom_reminders (user_id, text, reminder_datetime)
            VALUES (?, ?, ?)
        """, (user_id, text, reminder_datetime))
        conn.commit()
        return cur.lastrowid


def get_custom_reminder(conn, reminder_id: int):
    """Get a custom reminder by ID."""
    ensure_tables(conn)
    placeholder = "%s" if DB_TYPE == "postgresql" else "?"
    
    if DB_TYPE == "postgresql":
        import psycopg2.extras
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(f"SELECT * FROM custom_reminders WHERE id = {placeholder}", (reminder_id,))
        result = cur.fetchone()
        if result:
            from db_adapter import Row
            return Row(dict(result))
        return None
    else:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM custom_reminders WHERE id = {placeholder}", (reminder_id,))
        return cur.fetchone()


def get_all_custom_reminders_for_user(conn, user_id: int) -> List:
    """Get all custom reminders for a specific user."""
    ensure_tables(conn)
    placeholder = "%s" if DB_TYPE == "postgresql" else "?"
    
    if DB_TYPE == "postgresql":
        import psycopg2.extras
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(f"SELECT * FROM custom_reminders WHERE user_id = {placeholder} ORDER BY reminder_datetime", (user_id,))
        results = cur.fetchall()
        from db_adapter import Row
        return [Row(dict(r)) for r in results]
    else:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM custom_reminders WHERE user_id = {placeholder} ORDER BY reminder_datetime", (user_id,))
        return cur.fetchall()


def delete_custom_reminder(conn, reminder_id: int, user_id: int) -> bool:
    """Delete a custom reminder. Returns True if deleted, False if not found or not owned by user."""
    ensure_tables(conn)
    cur = conn.cursor()
    placeholder = "%s" if DB_TYPE == "postgresql" else "?"
    
    cur.execute(f"SELECT id FROM custom_reminders WHERE id = {placeholder} AND user_id = {placeholder}", (reminder_id, user_id))
    if cur.fetchone() is None:
        return False
    cur.execute(f"DELETE FROM custom_reminders WHERE id = {placeholder} AND user_id = {placeholder}", (reminder_id, user_id))
    conn.commit()
    return True


def mark_custom_reminder_done(conn, reminder_id: int, user_id: int):
    """Mark a custom reminder as done for a user."""
    ensure_tables(conn)
    cur = conn.cursor()
    
    if DB_TYPE == "postgresql":
        cur.execute("""
            INSERT INTO custom_reminder_completions (reminder_id, user_id, completed_at)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (reminder_id, user_id) DO UPDATE SET completed_at = CURRENT_TIMESTAMP
        """, (reminder_id, user_id))
    else:
        cur.execute("""
            INSERT OR REPLACE INTO custom_reminder_completions (reminder_id, user_id, completed_at)
            VALUES (?, ?, datetime('now'))
        """, (reminder_id, user_id))
    conn.commit()


def mark_custom_reminder_undone(conn, reminder_id: int, user_id: int):
    """Mark a custom reminder as not done for a user."""
    ensure_tables(conn)
    cur = conn.cursor()
    placeholder = "%s" if DB_TYPE == "postgresql" else "?"
    cur.execute(f"DELETE FROM custom_reminder_completions WHERE reminder_id = {placeholder} AND user_id = {placeholder}", (reminder_id, user_id))
    conn.commit()


def is_custom_reminder_done_for_user(conn, reminder_id: int, user_id: int) -> bool:
    """Check if a custom reminder is marked as done for a user."""
    ensure_tables(conn)
    cur = conn.cursor()
    placeholder = "%s" if DB_TYPE == "postgresql" else "?"
    cur.execute(f"SELECT 1 FROM custom_reminder_completions WHERE reminder_id = {placeholder} AND user_id = {placeholder}", (reminder_id, user_id))
    return cur.fetchone() is not None


def insert_faq_entry(conn, question: str, answer: str) -> int:
    """Insert a FAQ entry."""
    ensure_tables(conn)
    cur = conn.cursor()
    current_ts = get_current_timestamp()
    
    if DB_TYPE == "postgresql":
        cur.execute(f"""
            INSERT INTO faq_entries (question, answer, created_at, updated_at)
            VALUES (%s, %s, {current_ts}, {current_ts})
            RETURNING id
        """, (question, answer))
        result = cur.fetchone()
        conn.commit()
        return result[0] if result else None
    else:
        cur.execute(f"""
            INSERT INTO faq_entries (question, answer, created_at, updated_at)
            VALUES (?, ?, {current_ts}, {current_ts})
        """, (question, answer))
        conn.commit()
        return cur.lastrowid


def get_faq_entry(conn, faq_id: int):
    """Get a FAQ entry by ID."""
    ensure_tables(conn)
    placeholder = "%s" if DB_TYPE == "postgresql" else "?"
    
    if DB_TYPE == "postgresql":
        import psycopg2.extras
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(f"SELECT * FROM faq_entries WHERE id = {placeholder}", (faq_id,))
        result = cur.fetchone()
        if result:
            from db_adapter import Row
            return Row(dict(result))
        return None
    else:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM faq_entries WHERE id = {placeholder}", (faq_id,))
        return cur.fetchone()


def get_all_faq_entries(conn) -> List:
    """Get all FAQ entries."""
    ensure_tables(conn)
    
    if DB_TYPE == "postgresql":
        import psycopg2.extras
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM faq_entries ORDER BY id")
        results = cur.fetchall()
        from db_adapter import Row
        return [Row(dict(r)) for r in results]
    else:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM faq_entries ORDER BY id")
        return cur.fetchall()


def update_faq_entry(conn, faq_id: int, question: str, answer: str) -> bool:
    """Update a FAQ entry."""
    ensure_tables(conn)
    cur = conn.cursor()
    current_ts = get_current_timestamp()
    placeholder = "%s" if DB_TYPE == "postgresql" else "?"
    
    cur.execute(f"""
        UPDATE faq_entries
        SET question = {placeholder}, answer = {placeholder}, updated_at = {current_ts}
        WHERE id = {placeholder}
    """, (question, answer, faq_id))
    conn.commit()
    return cur.rowcount > 0


def delete_faq_entry(conn, faq_id: int) -> bool:
    """Delete a FAQ entry."""
    ensure_tables(conn)
    cur = conn.cursor()
    placeholder = "%s" if DB_TYPE == "postgresql" else "?"
    cur.execute(f"DELETE FROM faq_entries WHERE id = {placeholder}", (faq_id,))
    conn.commit()
    return cur.rowcount > 0


def get_notification_settings(conn, user_id: int) -> Optional:
    """Get notification settings for a user. Returns None if not set (defaults to all enabled)."""
    ensure_tables(conn)
    placeholder = "%s" if DB_TYPE == "postgresql" else "?"
    
    if DB_TYPE == "postgresql":
        import psycopg2.extras
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(f"SELECT * FROM notification_settings WHERE user_id = {placeholder}", (user_id,))
        result = cur.fetchone()
        if result:
            from db_adapter import Row
            return Row(dict(result))
        return None
    else:
        if conn.row_factory is None:
            conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM notification_settings WHERE user_id = {placeholder}", (user_id,))
        return cur.fetchone()

def get_notification_setting(conn, user_id: int, setting_type: str) -> bool:
    """
    Get a specific notification setting for a user.
    setting_type: 'homework_reminders', 'manual_reminders', or 'custom_reminders'
    Returns True if enabled (default), False if disabled.
    """
    ensure_tables(conn)
    settings = get_notification_settings(conn, user_id)
    if not settings:
        return True  
    column_name = f"{setting_type}_enabled"
    try:
        return bool(settings[column_name])
    except (KeyError, TypeError):
        return True  

def set_notification_setting(conn, user_id: int, setting_type: str, enabled: bool) -> bool:
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
    placeholder = "%s" if DB_TYPE == "postgresql" else "?"
    
    # Check if record exists
    cur.execute(f"SELECT 1 FROM notification_settings WHERE user_id = {placeholder}", (user_id,))
    exists = cur.fetchone() is not None
    
    if DB_TYPE == "postgresql":
        # PostgreSQL: Use ON CONFLICT
        cur.execute(f"""
            INSERT INTO notification_settings (user_id, homework_reminders_enabled, manual_reminders_enabled, 
                                              custom_reminders_enabled, updated_at)
            VALUES (%s, 1, 1, 1, %s)
            ON CONFLICT (user_id) DO UPDATE SET {column_name} = %s, updated_at = %s
        """, (user_id, updated_at, enabled_int, updated_at))
    else:
        # SQLite
        if exists:
            cur.execute(f"UPDATE notification_settings SET {column_name} = ?, updated_at = ? WHERE user_id = ?",
                       (enabled_int, updated_at, user_id))
        else:
            cur.execute("""
                INSERT INTO notification_settings (user_id, homework_reminders_enabled, manual_reminders_enabled, 
                                                  custom_reminders_enabled, updated_at)
                VALUES (?, 1, 1, 1, ?)
            """, (user_id, updated_at))
            cur.execute(f"UPDATE notification_settings SET {column_name} = ?, updated_at = ? WHERE user_id = ?",
                       (enabled_int, updated_at, user_id))
    conn.commit()
    return True

def enable_all_notifications(conn, user_id: int) -> bool:
    """Enable all notifications for a user."""
    ensure_tables(conn)
    cur = conn.cursor()
    from datetime import datetime
    updated_at = datetime.now().isoformat()
    placeholder = "%s" if DB_TYPE == "postgresql" else "?"
    
    cur.execute(f"SELECT 1 FROM notification_settings WHERE user_id = {placeholder}", (user_id,))
    exists = cur.fetchone() is not None
    
    if DB_TYPE == "postgresql":
        cur.execute("""
            INSERT INTO notification_settings (user_id, homework_reminders_enabled, manual_reminders_enabled, 
                                              custom_reminders_enabled, updated_at)
            VALUES (%s, 1, 1, 1, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                homework_reminders_enabled = 1,
                manual_reminders_enabled = 1,
                custom_reminders_enabled = 1,
                updated_at = EXCLUDED.updated_at
        """, (user_id, updated_at))
    else:
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

def disable_all_notifications(conn, user_id: int) -> bool:
    """Disable all notifications for a user."""
    ensure_tables(conn)
    cur = conn.cursor()
    from datetime import datetime
    updated_at = datetime.now().isoformat()
    placeholder = "%s" if DB_TYPE == "postgresql" else "?"
    
    cur.execute(f"SELECT 1 FROM notification_settings WHERE user_id = {placeholder}", (user_id,))
    exists = cur.fetchone() is not None
    
    if DB_TYPE == "postgresql":
        cur.execute("""
            INSERT INTO notification_settings (user_id, homework_reminders_enabled, manual_reminders_enabled, 
                                              custom_reminders_enabled, updated_at)
            VALUES (%s, 0, 0, 0, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                homework_reminders_enabled = 0,
                manual_reminders_enabled = 0,
                custom_reminders_enabled = 0,
                updated_at = EXCLUDED.updated_at
        """, (user_id, updated_at))
    else:
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


if __name__ == "__main__":
    conn = get_conn()
    ensure_tables(conn)
    print("DB initialized at", os.path.join(os.path.dirname(__file__), DEFAULT_DB_NAME))
    conn.close()
