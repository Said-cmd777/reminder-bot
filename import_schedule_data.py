#!/usr/bin/env python3
"""
Import schedule data using Python instead of sqlite3 CLI.
Fixes Replit sqlite3 issue.
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def import_schedule_data():
    """Import schedule data from SQL file."""
    try:
        print("🔄 Importing schedule data...")
        
        # Try to import db module
        from db import get_conn, ensure_tables
        
        DB_PATH = "reminders.db"
        conn = get_conn(DB_PATH)
        ensure_tables(conn)
        cur = conn.cursor()
        
        # Read SQL file
        sql_file = "schedule_data.sql"
        if not os.path.exists(sql_file):
            print(f"❌ File not found: {sql_file}")
            sys.exit(1)
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Parse and execute SQL statements
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip() and not stmt.strip().startswith('--')]
        
        print(f"📋 Found {len(statements)} SQL statements")
        
        for i, statement in enumerate(statements, 1):
            try:
                # Skip comments
                if statement.startswith('--'):
                    continue
                
                print(f"   [{i}/{len(statements)}] Executing: {statement[:60]}...")
                cur.execute(statement)
                conn.commit()
            except Exception as e:
                print(f"   ⚠️  Warning: {e}")
                # Continue on error
                continue
        
        conn.close()
        
        print("\n✅ Data import completed!")
        print("\n📊 Verifying import...")
        
        # Verify
        conn = get_conn(DB_PATH)
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) as count FROM weekly_schedule_classes")
        classes_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) as count FROM alternating_weeks_config")
        config_count = cur.fetchone()[0]
        
        conn.close()
        
        print(f"   ✅ Schedule classes: {classes_count}")
        print(f"   ✅ Alternating configs: {config_count}")
        
        if classes_count > 0 and config_count > 0:
            print("\n✅ Import successful! Ready to start bot.")
            return 0
        else:
            print("\n⚠️  Some data might not have been imported correctly.")
            return 1
            
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("   Make sure you're in the correct directory with db.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(import_schedule_data())
