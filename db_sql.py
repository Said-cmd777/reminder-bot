"""
SQL syntax adapter - converts SQL between SQLite and PostgreSQL syntax.
"""

from db_config import DB_TYPE


def get_create_table_sql() -> dict:
    """
    Get CREATE TABLE statements for the current database type.
    
    Returns:
        dict: Table name -> CREATE TABLE SQL
    """
    
    if DB_TYPE == "sqlite":
        return _get_sqlite_schema()
    else:
        return _get_postgresql_schema()


def _get_sqlite_schema() -> dict:
    """SQLite schema definitions."""
    return {
        "homeworks": """
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
            )
        """,
        "users": """
            CREATE TABLE IF NOT EXISTS users (
              user_id INTEGER UNIQUE NOT NULL,
              started_at TEXT,
              username TEXT,
              first_name TEXT,
              last_name TEXT,
              registered_at TEXT,
              display_name TEXT,
              group_number TEXT
            )
        """,
        "homework_completions": """
            CREATE TABLE IF NOT EXISTS homework_completions (
              hw_id INTEGER NOT NULL,
              user_id INTEGER NOT NULL,
              completed_at TEXT DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (hw_id, user_id),
              FOREIGN KEY (hw_id) REFERENCES homeworks(id) ON DELETE CASCADE
            )
        """,
        "custom_reminders": """
            CREATE TABLE IF NOT EXISTS custom_reminders (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL,
              text TEXT NOT NULL,
              reminder_datetime TEXT NOT NULL,
              created_at TEXT DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """,
        "custom_reminder_completions": """
            CREATE TABLE IF NOT EXISTS custom_reminder_completions (
              reminder_id INTEGER NOT NULL,
              user_id INTEGER NOT NULL,
              completed_at TEXT DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (reminder_id, user_id),
              FOREIGN KEY (reminder_id) REFERENCES custom_reminders(id) ON DELETE CASCADE
            )
        """,
        "faq_entries": """
            CREATE TABLE IF NOT EXISTS faq_entries (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              question TEXT NOT NULL,
              answer TEXT NOT NULL,
              created_at TEXT DEFAULT CURRENT_TIMESTAMP,
              updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """,
        "weekly_schedule_classes": """
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
            )
        """,
        "schedule_locations": """
            CREATE TABLE IF NOT EXISTS schedule_locations (
              location_name TEXT PRIMARY KEY,
              maps_url TEXT,
              created_at TEXT DEFAULT CURRENT_TIMESTAMP,
              updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """,
        "alternating_weeks_config": """
            CREATE TABLE IF NOT EXISTS alternating_weeks_config (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              alternating_key TEXT UNIQUE NOT NULL,
              reference_date TEXT NOT NULL,
              description TEXT,
              created_at TEXT DEFAULT CURRENT_TIMESTAMP,
              updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """,
        "notification_settings": """
            CREATE TABLE IF NOT EXISTS notification_settings (
              user_id INTEGER PRIMARY KEY,
              homework_reminders_enabled INTEGER DEFAULT 1,
              manual_reminders_enabled INTEGER DEFAULT 1,
              custom_reminders_enabled INTEGER DEFAULT 1,
              updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """
    }


def _get_postgresql_schema() -> dict:
    """PostgreSQL schema definitions."""
    return {
        "homeworks": """
            CREATE TABLE IF NOT EXISTS homeworks (
              id SERIAL PRIMARY KEY,
              subject TEXT NOT NULL,
              description TEXT,
              due_at TIMESTAMP NOT NULL,
              pdf_type TEXT,
              pdf_value TEXT,
              conditions TEXT,
              created_by INTEGER,
              chat_id INTEGER,
              done INTEGER DEFAULT 0,
              reminders TEXT,
              target_user_id INTEGER,
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        "users": """
            CREATE TABLE IF NOT EXISTS users (
              user_id BIGINT UNIQUE NOT NULL,
              started_at TIMESTAMP,
              username TEXT,
              first_name TEXT,
              last_name TEXT,
              registered_at TIMESTAMP,
              display_name TEXT,
              group_number TEXT
            )
        """,
        "homework_completions": """
            CREATE TABLE IF NOT EXISTS homework_completions (
              hw_id INTEGER NOT NULL,
              user_id BIGINT NOT NULL,
              completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (hw_id, user_id),
              FOREIGN KEY (hw_id) REFERENCES homeworks(id) ON DELETE CASCADE
            )
        """,
        "custom_reminders": """
            CREATE TABLE IF NOT EXISTS custom_reminders (
              id SERIAL PRIMARY KEY,
              user_id BIGINT NOT NULL,
              text TEXT NOT NULL,
              reminder_datetime TIMESTAMP NOT NULL,
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """,
        "custom_reminder_completions": """
            CREATE TABLE IF NOT EXISTS custom_reminder_completions (
              reminder_id INTEGER NOT NULL,
              user_id BIGINT NOT NULL,
              completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (reminder_id, user_id),
              FOREIGN KEY (reminder_id) REFERENCES custom_reminders(id) ON DELETE CASCADE
            )
        """,
        "faq_entries": """
            CREATE TABLE IF NOT EXISTS faq_entries (
              id SERIAL PRIMARY KEY,
              question TEXT NOT NULL,
              answer TEXT NOT NULL,
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        "weekly_schedule_classes": """
            CREATE TABLE IF NOT EXISTS weekly_schedule_classes (
              id SERIAL PRIMARY KEY,
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
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              UNIQUE(group_number, day_name, time_start, course)
            )
        """,
        "schedule_locations": """
            CREATE TABLE IF NOT EXISTS schedule_locations (
              location_name TEXT PRIMARY KEY,
              maps_url TEXT,
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        "alternating_weeks_config": """
            CREATE TABLE IF NOT EXISTS alternating_weeks_config (
              id SERIAL PRIMARY KEY,
              alternating_key TEXT UNIQUE NOT NULL,
              reference_date TEXT NOT NULL,
              description TEXT,
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        "notification_settings": """
            CREATE TABLE IF NOT EXISTS notification_settings (
              user_id BIGINT PRIMARY KEY,
              homework_reminders_enabled INTEGER DEFAULT 1,
              manual_reminders_enabled INTEGER DEFAULT 1,
              custom_reminders_enabled INTEGER DEFAULT 1,
              updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """
    }


def get_current_timestamp() -> str:
    """
    Get the SQL for current timestamp based on DB type.
    
    Returns:
        str: SQL expression for current timestamp
    """
    if DB_TYPE == "sqlite":
        return "datetime('now')"
    else:
        return "CURRENT_TIMESTAMP"


def get_insert_or_replace_sql(table: str, columns: list, placeholders: list) -> str:
    """
    Get INSERT OR REPLACE SQL for the current database type.
    
    Args:
        table: Table name
        columns: List of column names
        placeholders: List of placeholders (?, ?, ?)
    
    Returns:
        str: SQL statement
    """
    cols_str = ", ".join(columns)
    placeholders_str = ", ".join(["%s" if DB_TYPE == "postgresql" else "?" for _ in placeholders])
    
    if DB_TYPE == "sqlite":
        return f"INSERT OR REPLACE INTO {table} ({cols_str}) VALUES ({placeholders_str})"
    else:
        # PostgreSQL uses ON CONFLICT ... DO UPDATE
        # This needs to know the primary key - we'll handle this per table
        if table == "homework_completions":
            update_clause = "ON CONFLICT (hw_id, user_id) DO UPDATE SET completed_at = EXCLUDED.completed_at"
        elif table == "custom_reminder_completions":
            update_clause = "ON CONFLICT (reminder_id, user_id) DO UPDATE SET completed_at = EXCLUDED.completed_at"
        elif table == "notification_settings":
            # Get all columns except user_id for update
            update_cols = [c for c in columns if c != "user_id"]
            update_parts = [f"{c} = EXCLUDED.{c}" for c in update_cols]
            update_clause = f"ON CONFLICT (user_id) DO UPDATE SET {', '.join(update_parts)}"
        elif table == "users":
            update_cols = [c for c in columns if c != "user_id"]
            update_parts = [f"{c} = EXCLUDED.{c}" for c in update_cols]
            update_clause = f"ON CONFLICT (user_id) DO UPDATE SET {', '.join(update_parts)}"
        else:
            update_clause = ""
        
        return f"INSERT INTO {table} ({cols_str}) VALUES ({placeholders_str}) {update_clause}"


def convert_params(params: tuple) -> tuple:
    """
    Convert query parameters for the current database type.
    
    For PostgreSQL, converts ? placeholders to %s (this is handled by the caller).
    """
    return params


def get_returning_clause(column: str = "id") -> str:
    """
    Get RETURNING clause for INSERT statements (PostgreSQL).
    
    Returns:
        str: RETURNING clause or empty string for SQLite
    """
    if DB_TYPE == "postgresql":
        return f" RETURNING {column}"
    else:
        return ""
