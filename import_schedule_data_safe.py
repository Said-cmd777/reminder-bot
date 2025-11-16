#!/usr/bin/env python3
"""
Alternative schedule data importer - uses direct SQL parsing without db module.
This avoids Replit's sqlite3 binary issues.
"""
import sqlite3
import os
import sys

def parse_sql_statements(sql_content):
    """Parse SQL content into individual statements."""
    statements = []
    current = ""
    in_string = False
    string_char = None
    
    for char in sql_content:
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
            if stmt and not stmt.startswith('--'):
                statements.append(stmt[:-1])  # Remove trailing semicolon
            current = ""
    
    return statements

def import_schedule_data_safe():
    """Import schedule data with error handling."""
    try:
        print("🔄 Importing schedule data (safe mode)...\n")
        
        SQL_FILE = "schedule_data.sql"
        DB_PATH = "reminders.db"
        
        # Check if SQL file exists
        if not os.path.exists(SQL_FILE):
            print(f"❌ File not found: {SQL_FILE}")
            return False
        
        # Read SQL file
        print(f"📖 Reading {SQL_FILE}...")
        with open(SQL_FILE, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Parse SQL statements
        print("🔍 Parsing SQL statements...")
        statements = parse_sql_statements(sql_content)
        print(f"   Found {len(statements)} statements\n")
        
        # Connect to database
        print(f"🗄️  Connecting to {DB_PATH}...")
        conn = sqlite3.connect(DB_PATH, timeout=30)
        cur = conn.cursor()
        
        # Execute each statement
        success_count = 0
        error_count = 0
        
        for i, stmt in enumerate(statements, 1):
            if not stmt.strip():
                continue
            
            try:
                print(f"   [{i:2d}/{len(statements)}] ", end="")
                
                # Truncate display
                display_stmt = stmt[:50].replace('\n', ' ')
                print(f"{display_stmt}...", end=" ")
                
                cur.execute(stmt)
                print("✅")
                success_count += 1
                
            except sqlite3.IntegrityError as e:
                # This might be OK - could be duplicate insert
                print(f"⚠️  (Duplicate/Constraint)")
                error_count += 1
            except Exception as e:
                print(f"❌ {str(e)[:30]}")
                error_count += 1
        
        # Commit changes
        print("\n💾 Committing changes...")
        conn.commit()
        
        # Verify import
        print("\n📊 Verifying import...\n")
        
        cur.execute("SELECT COUNT(*) FROM weekly_schedule_classes")
        classes_count = cur.fetchone()[0]
        print(f"   📚 Schedule classes: {classes_count}")
        
        cur.execute("SELECT COUNT(*) FROM alternating_weeks_config")
        config_count = cur.fetchone()[0]
        print(f"   🔄 Alternating configs: {config_count}")
        
        # Check Group 04 specifically
        cur.execute("""
            SELECT COUNT(*) FROM weekly_schedule_classes 
            WHERE group_number='04' AND is_alternating=1
        """)
        group04_alt = cur.fetchone()[0]
        print(f"   ✨ Group 04 alternating: {group04_alt}")
        
        conn.close()
        
        print(f"\n✅ Import completed!")
        print(f"   Successful: {success_count}")
        print(f"   Warnings: {error_count}")
        
        if classes_count > 0:
            print("\n🎉 Database is ready! Start bot with: python bot.py")
            return True
        else:
            print("\n⚠️  No data was imported!")
            return False
            
    except sqlite3.DatabaseError as e:
        print(f"\n❌ Database Error: {e}")
        print("   Try deleting the database and trying again:")
        print("   rm reminders.db")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = import_schedule_data_safe()
    sys.exit(0 if success else 1)
