#!/usr/bin/env python3
"""Export schedule data to SQL insert statements."""
import sqlite3
import sys

DB_PATH = "reminders.db"

def export_schedule_data():
    """Export all schedule classes and alternating config as SQL inserts."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Get all schedule classes
        cur.execute("""
            SELECT group_number, day_name, time_start, time_end, course, location, 
                   class_type, is_alternating, alternating_key
            FROM weekly_schedule_classes
            ORDER BY group_number, 
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
        
        classes = cur.fetchall()
        
        # Get alternating week config
        cur.execute("""
            SELECT alternating_key, reference_date, description
            FROM alternating_weeks_config
            ORDER BY alternating_key
        """)
        
        configs = cur.fetchall()
        conn.close()
        
        # Write to file
        with open("schedule_data.sql", "w", encoding="utf-8") as f:
            f.write("-- Schedule Data Export\n")
            f.write("-- Generated for Replit sync\n\n")
            
            # Delete existing data first
            f.write("DELETE FROM weekly_schedule_classes;\n")
            f.write("DELETE FROM alternating_weeks_config;\n\n")
            
            # Insert classes
            f.write("-- Insert Classes\n")
            for cls in classes:
                alt_key = f"'{cls['alternating_key']}'" if cls['alternating_key'] else "NULL"
                f.write(
                    f"INSERT INTO weekly_schedule_classes "
                    f"(group_number, day_name, time_start, time_end, course, location, class_type, is_alternating, alternating_key) "
                    f"VALUES ('{cls['group_number']}', '{cls['day_name']}', '{cls['time_start']}', '{cls['time_end']}', "
                    f"'{cls['course']}', '{cls['location']}', '{cls['class_type']}', {cls['is_alternating']}, {alt_key});\n"
                )
            
            f.write("\n-- Insert Alternating Week Configuration\n")
            for cfg in configs:
                desc = cfg['description'].replace("'", "''") if cfg['description'] else ""
                f.write(
                    f"INSERT INTO alternating_weeks_config "
                    f"(alternating_key, reference_date, description) "
                    f"VALUES ('{cfg['alternating_key']}', '{cfg['reference_date']}', '{desc}');\n"
                )
        
        print("✅ Data exported to: schedule_data.sql")
        print(f"   - {len(classes)} schedule classes")
        print(f"   - {len(configs)} alternating configurations")
        print("\n📝 Next steps on Replit:")
        print("   1. Push this file to GitHub:")
        print("      git add schedule_data.sql")
        print("      git commit -m 'Add schedule data sync script'")
        print("      git push origin main")
        print("   2. On Replit, pull and run:")
        print("      git pull origin main")
        print("      sqlite3 reminders.db < schedule_data.sql")
        print("      python bot.py")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    export_schedule_data()
