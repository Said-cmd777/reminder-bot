#!/usr/bin/env python3
"""Check database status and alternating classes."""
import sqlite3
import sys

DB_PATH = "reminders.db"

def check_database():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        print("=" * 80)
        print("🔍 DATABASE STATUS CHECK")
        print("=" * 80)
        
        # Check if table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='weekly_schedule_classes'")
        if not cur.fetchone():
            print("\n❌ Table 'weekly_schedule_classes' does NOT exist!")
            print("   Creating table...")
            from db import ensure_tables
            ensure_tables(conn)
            print("   ✅ Table created")
        else:
            print("\n✅ Table 'weekly_schedule_classes' exists")
        
        # Check total records
        cur.execute("SELECT COUNT(*) as count FROM weekly_schedule_classes")
        total = cur.fetchone()['count']
        print(f"\n📊 Total classes in database: {total}")
        
        # Check Group 04 records
        print("\n" + "=" * 80)
        print("📋 GROUP 04 SCHEDULE")
        print("=" * 80)
        
        cur.execute("""
            SELECT id, day_name, time_start, time_end, course, class_type, 
                   is_alternating, alternating_key 
            FROM weekly_schedule_classes 
            WHERE group_number='04' 
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
                time_start
        """)
        
        rows = cur.fetchall()
        if not rows:
            print("\n❌ NO RECORDS FOUND for Group 04!")
        else:
            print(f"\n✅ Found {len(rows)} classes for Group 04:\n")
            
            current_day = None
            for row in rows:
                day = row['day_name'].upper()
                if day != current_day:
                    print(f"\n📅 {day}")
                    current_day = day
                
                alt_flag = "🔄" if row['is_alternating'] else "  "
                alt_info = f" [key: {row['alternating_key']}]" if row['alternating_key'] else ""
                
                print(f"  {alt_flag} {row['time_start']}-{row['time_end']} | "
                      f"{row['course']:20} | {row['class_type']:20}{alt_info}")
        
        # Check alternating classes
        print("\n" + "=" * 80)
        print("🔄 ALTERNATING CLASSES FOR GROUP 04")
        print("=" * 80)
        
        cur.execute("""
            SELECT course, class_type, alternating_key, day_name 
            FROM weekly_schedule_classes 
            WHERE group_number='04' AND is_alternating=1
            ORDER BY alternating_key
        """)
        
        alt_rows = cur.fetchall()
        if not alt_rows:
            print("\n❌ NO ALTERNATING CLASSES FOUND!")
            print("   This is the problem! Lab sessions are not marked as alternating.")
        else:
            print(f"\n✅ Found {len(alt_rows)} alternating classes:\n")
            for row in alt_rows:
                print(f"  🔬 {row['course']:20} | {row['class_type']:20} | {row['day_name']}")
                print(f"     Key: {row['alternating_key']}")
        
        # Check alternating week config
        print("\n" + "=" * 80)
        print("⏰ ALTERNATING WEEK CONFIGURATION")
        print("=" * 80)
        
        cur.execute("SELECT * FROM alternating_weeks_config")
        config_rows = cur.fetchall()
        
        if not config_rows:
            print("\n❌ NO ALTERNATING WEEK CONFIG FOUND!")
        else:
            print(f"\n✅ Found {len(config_rows)} configurations:\n")
            for row in config_rows:
                print(f"  Key: {row['alternating_key']}")
                print(f"  Reference Date: {row['reference_date']}")
                print(f"  Description: {row['description']}\n")
        
        conn.close()
        
        print("=" * 80)
        print("✅ DATABASE CHECK COMPLETED")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    check_database()
