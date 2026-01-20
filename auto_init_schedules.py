#!/usr/bin/env python3
"""
Auto-initialization module for weekly schedule data.
Automatically restores schedule data from schedule_data.sql if database is empty.
This is critical for cloud platforms with ephemeral storage (e.g., Render).
"""
import sqlite3
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def _ensure_schedule_tables(cur: sqlite3.Cursor):
    """
    Ensure schedule-related tables exist in the database.
    This creates the tables if they don't already exist.
    
    Args:
        cur: Database cursor
    """
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
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS alternating_weeks_config (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      alternating_key TEXT UNIQUE NOT NULL,
      reference_date TEXT NOT NULL,
      description TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)


def parse_sql_statements(sql_content: str) -> list:
    """
    Parse SQL content into individual statements.
    Handles strings properly to avoid splitting on semicolons inside quotes.
    Handles SQL comments (-- style) by filtering them out before parsing.
    
    Args:
        sql_content: Raw SQL file content
        
    Returns:
        List of SQL statements (without trailing semicolons)
    """
    # First, remove SQL comments (lines starting with --)
    lines = sql_content.split('\n')
    cleaned_lines = []
    for line in lines:
        # Remove comment lines but preserve empty lines for readability
        if not line.strip().startswith('--'):
            cleaned_lines.append(line)
    
    cleaned_content = '\n'.join(cleaned_lines)
    
    # Now parse statements
    statements = []
    current = ""
    in_string = False
    string_char = None
    
    for char in cleaned_content:
        if char in ('"', "'") and (not in_string or string_char == char):
            if in_string and string_char == char:
                in_string = False
                string_char = None
            elif not in_string:
                in_string = True
                string_char = char
        
        current += char
        
        if char == ';' and not in_string:
            stmt = current.strip()
            # Skip empty statements
            if stmt:
                statements.append(stmt[:-1])  # Remove trailing semicolon
            current = ""
    
    return statements


def check_schedule_data_exists(db_path: str) -> bool:
    """
    Check if schedule data exists in the database.
    
    Args:
        db_path: Path to the SQLite database
        
    Returns:
        True if schedule data exists, False otherwise
    """
    try:
        if not os.path.exists(db_path):
            logger.info(f"Database file does not exist: {db_path}")
            return False
        
        conn = sqlite3.connect(db_path, timeout=30)
        cur = conn.cursor()
        
        # Check if tables exist
        cur.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='weekly_schedule_classes'
        """)
        if not cur.fetchone():
            logger.info("Table 'weekly_schedule_classes' does not exist")
            conn.close()
            return False
        
        # Check if there's any schedule data
        cur.execute("SELECT COUNT(*) FROM weekly_schedule_classes")
        count = cur.fetchone()[0]
        conn.close()
        
        if count == 0:
            logger.info("Schedule table exists but is empty")
            return False
        
        logger.info(f"Schedule data exists: {count} classes found")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Error checking schedule data: {e}")
        return False


def restore_schedule_data(db_path: str, sql_file: str = "schedule_data.sql") -> bool:
    """
    Restore schedule data from SQL file into the database.
    
    Args:
        db_path: Path to the SQLite database
        sql_file: Path to the SQL file containing schedule data
        
    Returns:
        True if restoration was successful, False otherwise
    """
    try:
        logger.info(f"🔄 Starting schedule data restoration from {sql_file}")
        
        # Check if SQL file exists
        if not os.path.exists(sql_file):
            # Try with absolute path
            script_dir = os.path.dirname(os.path.abspath(__file__))
            sql_file = os.path.join(script_dir, sql_file)
            
            if not os.path.exists(sql_file):
                logger.error(f"❌ SQL file not found: {sql_file}")
                return False
        
        # Read SQL file
        logger.info(f"📖 Reading {sql_file}...")
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Parse SQL statements
        logger.info("🔍 Parsing SQL statements...")
        statements = parse_sql_statements(sql_content)
        logger.info(f"   Found {len(statements)} statements")
        
        if not statements:
            logger.warning("⚠️  No SQL statements found in file")
            return False
        
        # Connect to database
        logger.info(f"🗄️  Connecting to {db_path}...")
        conn = sqlite3.connect(db_path, timeout=30)
        cur = conn.cursor()
        
        # Ensure tables exist before inserting data
        logger.info("📋 Ensuring database tables exist...")
        _ensure_schedule_tables(cur)
        conn.commit()
        
        # Execute each statement
        success_count = 0
        error_count = 0
        
        for i, stmt in enumerate(statements, 1):
            if not stmt.strip():
                continue
            
            try:
                cur.execute(stmt)
                success_count += 1
                
            except sqlite3.IntegrityError as e:
                # This might be OK - could be duplicate insert
                logger.debug(f"   Statement {i}: Integrity constraint (likely duplicate)")
                error_count += 1
                
            except Exception as e:
                logger.warning(f"   Statement {i} failed: {str(e)[:50]}")
                error_count += 1
        
        # Commit changes
        logger.info("💾 Committing changes...")
        conn.commit()
        
        # Verify restoration
        logger.info("📊 Verifying restoration...")
        
        cur.execute("SELECT COUNT(*) FROM weekly_schedule_classes")
        classes_count = cur.fetchone()[0]
        logger.info(f"   📚 Schedule classes: {classes_count}")
        
        cur.execute("SELECT COUNT(*) FROM alternating_weeks_config")
        config_count = cur.fetchone()[0]
        logger.info(f"   🔄 Alternating configs: {config_count}")
        
        # Check each group
        for group in ['01', '02', '03', '04']:
            cur.execute("""
                SELECT COUNT(*) FROM weekly_schedule_classes 
                WHERE group_number=?
            """, (group,))
            group_count = cur.fetchone()[0]
            logger.info(f"   ✨ Group {group}: {group_count} classes")
        
        conn.close()
        
        logger.info(f"✅ Schedule data restoration completed!")
        logger.info(f"   Successful statements: {success_count}")
        if error_count > 0:
            logger.info(f"   Warnings/duplicates: {error_count}")
        
        return classes_count > 0
        
    except sqlite3.Error as e:
        logger.error(f"❌ Database error during restoration: {e}")
        return False
        
    except Exception as e:
        logger.error(f"❌ Error during restoration: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def auto_init_schedules(db_path: str, sql_file: str = "schedule_data.sql") -> bool:
    """
    Auto-initialize schedule data if needed.
    This function is idempotent - safe to call multiple times.
    
    Args:
        db_path: Path to the SQLite database
        sql_file: Path to the SQL file containing schedule data
        
    Returns:
        True if data is available (either already existed or was restored), False otherwise
    """
    logger.info("🔍 Checking schedule data availability...")
    
    # Check if schedule data already exists
    if check_schedule_data_exists(db_path):
        logger.info("✅ Schedule data already present - no restoration needed")
        return True
    
    # Data doesn't exist, try to restore it
    logger.info("⚠️  Schedule data missing - attempting automatic restoration...")
    success = restore_schedule_data(db_path, sql_file)
    
    if success:
        logger.info("✅ Schedule data automatically restored")
        return True
    else:
        logger.error("❌ Failed to restore schedule data")
        logger.error("   Weekly schedules may not work properly!")
        return False


if __name__ == "__main__":
    # For testing purposes
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    db_path = sys.argv[1] if len(sys.argv) > 1 else "reminders.db"
    sql_file = sys.argv[2] if len(sys.argv) > 2 else "schedule_data.sql"
    
    success = auto_init_schedules(db_path, sql_file)
    sys.exit(0 if success else 1)
