
"""Database functions for weekly schedule management."""
import sqlite3
from typing import List, Optional, Dict, Any
from db import ensure_tables, get_conn
from db_utils import db_connection as _db_connection


def insert_schedule_class(conn: sqlite3.Connection, group_number: str, day_name: str,
                         time_start: str, time_end: str, course: str, location: str,
                         class_type: str, is_alternating: bool = False,
                         alternating_key: Optional[str] = None, display_order: int = 0) -> int:
    """Insert a new schedule class."""
    ensure_tables(conn)
    cur = conn.cursor()
    try:
        cur.execute("""
        INSERT INTO weekly_schedule_classes 
        (group_number, day_name, time_start, time_end, course, location, class_type, 
         is_alternating, alternating_key, display_order)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (group_number, day_name, time_start, time_end, course, location, class_type,
              1 if is_alternating else 0, alternating_key, display_order))
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        
        cur.execute("""
        UPDATE weekly_schedule_classes
        SET time_end = ?, location = ?, class_type = ?, is_alternating = ?,
            alternating_key = ?, display_order = ?, updated_at = CURRENT_TIMESTAMP
        WHERE group_number = ? AND day_name = ? AND time_start = ? AND course = ?
        """, (time_end, location, class_type, 1 if is_alternating else 0,
              alternating_key, display_order, group_number, day_name, time_start, course))
        conn.commit()
        cur.execute("SELECT id FROM weekly_schedule_classes WHERE group_number = ? AND day_name = ? AND time_start = ? AND course = ?",
                   (group_number, day_name, time_start, course))
        row = cur.fetchone()
        return row[0] if row else 0


def get_schedule_classes(conn: sqlite3.Connection, group_number: str, day_name: Optional[str] = None) -> List[sqlite3.Row]:
    """Get schedule classes for a group and optionally a specific day."""
    ensure_tables(conn)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    if day_name:
        cur.execute("""
        SELECT * FROM weekly_schedule_classes
        WHERE group_number = ? AND day_name = ?
        ORDER BY display_order, time_start
        """, (group_number, day_name))
    else:
        cur.execute("""
        SELECT * FROM weekly_schedule_classes
        WHERE group_number = ?
        ORDER BY 
          CASE day_name
            WHEN 'saturday' THEN 1
            WHEN 'sunday' THEN 2
            WHEN 'monday' THEN 3
            WHEN 'tuesday' THEN 4
            WHEN 'wednesday' THEN 5
            WHEN 'thursday' THEN 6
            WHEN 'friday' THEN 7
          END,
          display_order, time_start
        """, (group_number,))
    return cur.fetchall()


def get_schedule_class(conn: sqlite3.Connection, class_id: int) -> Optional[sqlite3.Row]:
    """Get a specific schedule class by ID."""
    ensure_tables(conn)
    cur = conn.cursor()
    cur.execute("SELECT * FROM weekly_schedule_classes WHERE id = ?", (class_id,))
    return cur.fetchone()


def update_schedule_class(conn: sqlite3.Connection, class_id: int, **kwargs) -> bool:
    """Update a schedule class. kwargs can contain: time_start, time_end, course, location, class_type, is_alternating, alternating_key, display_order"""
    ensure_tables(conn)
    cur = conn.cursor()
    
    allowed_fields = ['time_start', 'time_end', 'course', 'location', 'class_type', 
                     'is_alternating', 'alternating_key', 'display_order']
    updates = []
    values = []
    
    for field, value in kwargs.items():
        if field in allowed_fields:
            if field == 'is_alternating':
                updates.append(f"{field} = ?")
                values.append(1 if value else 0)
            else:
                updates.append(f"{field} = ?")
                values.append(value)
    
    if not updates:
        return False
    
    updates.append("updated_at = CURRENT_TIMESTAMP")
    values.append(class_id)
    
    sql = f"UPDATE weekly_schedule_classes SET {', '.join(updates)} WHERE id = ?"
    cur.execute(sql, values)
    conn.commit()
    return cur.rowcount > 0


def delete_schedule_class(conn: sqlite3.Connection, class_id: int) -> bool:
    """Delete a schedule class."""
    ensure_tables(conn)
    cur = conn.cursor()
    cur.execute("DELETE FROM weekly_schedule_classes WHERE id = ?", (class_id,))
    conn.commit()
    return cur.rowcount > 0


def insert_schedule_location(conn: sqlite3.Connection, location_name: str, maps_url: str) -> bool:
    """Insert or update a schedule location."""
    ensure_tables(conn)
    cur = conn.cursor()
    try:
        cur.execute("""
        INSERT INTO schedule_locations (location_name, maps_url)
        VALUES (?, ?)
        """, (location_name, maps_url))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        cur.execute("""
        UPDATE schedule_locations
        SET maps_url = ?, updated_at = CURRENT_TIMESTAMP
        WHERE location_name = ?
        """, (maps_url, location_name))
        conn.commit()
        return True


def get_schedule_locations(conn: sqlite3.Connection) -> Dict[str, str]:
    """Get all schedule locations as a dictionary."""
    ensure_tables(conn)
    cur = conn.cursor()
    cur.execute("SELECT location_name, maps_url FROM schedule_locations")
    return {row[0]: row[1] for row in cur.fetchall()}


def get_schedule_location(conn: sqlite3.Connection, location_name: str) -> Optional[str]:
    """Get maps URL for a location."""
    ensure_tables(conn)
    cur = conn.cursor()
    cur.execute("SELECT maps_url FROM schedule_locations WHERE location_name = ?", (location_name,))
    row = cur.fetchone()
    return row[0] if row else None


def delete_schedule_location(conn: sqlite3.Connection, location_name: str) -> bool:
    """Delete a schedule location."""
    ensure_tables(conn)
    cur = conn.cursor()
    cur.execute("DELETE FROM schedule_locations WHERE location_name = ?", (location_name,))
    conn.commit()
    return cur.rowcount > 0


def set_alternating_week_config(conn: sqlite3.Connection, alternating_key: str, reference_date: str, description: Optional[str] = None) -> bool:
    """Set configuration for alternating weeks."""
    ensure_tables(conn)
    cur = conn.cursor()
    try:
        cur.execute("""
        INSERT INTO alternating_weeks_config (alternating_key, reference_date, description)
        VALUES (?, ?, ?)
        """, (alternating_key, reference_date, description))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        cur.execute("""
        UPDATE alternating_weeks_config
        SET reference_date = ?, description = ?, updated_at = CURRENT_TIMESTAMP
        WHERE alternating_key = ?
        """, (reference_date, description, alternating_key))
        conn.commit()
        return True


def get_alternating_week_config(conn: sqlite3.Connection, alternating_key: str) -> Optional[sqlite3.Row]:
    """Get alternating week configuration."""
    ensure_tables(conn)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM alternating_weeks_config WHERE alternating_key = ?", (alternating_key,))
    return cur.fetchone()


def get_all_groups(conn: sqlite3.Connection) -> List[str]:
    """Get list of all group numbers in the database."""
    ensure_tables(conn)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT group_number FROM weekly_schedule_classes ORDER BY group_number")
    return [row[0] for row in cur.fetchall()]


def get_all_alternating_week_configs(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    """Get all alternating week configurations."""
    ensure_tables(conn)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM alternating_weeks_config ORDER BY alternating_key")
    return cur.fetchall()


def update_schedule_class_field(conn: sqlite3.Connection, class_id: int, field: str, value: Any) -> bool:
    """Update a specific field of a schedule class."""
    ensure_tables(conn)
    cur = conn.cursor()
    
    allowed_fields = ['time_start', 'time_end', 'course', 'location', 'class_type', 
                     'is_alternating', 'alternating_key', 'display_order']
    
    if field not in allowed_fields:
        return False
    
    if field == 'is_alternating':
        value = 1 if value else 0
    
    cur.execute(f"UPDATE weekly_schedule_classes SET {field} = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", 
                (value, class_id))
    conn.commit()
    return cur.rowcount > 0

