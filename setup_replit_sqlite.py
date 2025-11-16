#!/usr/bin/env python3
"""
Create database from scratch on Replit using pysqlite3-binary.
This avoids the glibc issue completely.
"""
import subprocess
import sys
import os

def install_and_setup():
    """Install pysqlite3-binary and setup database."""
    try:
        print("📦 Step 1: Installing pysqlite3-binary...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "pysqlite3-binary", "-q"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"⚠️  Installation warning: {result.stderr[:100]}")
        else:
            print("✅ Installed successfully")
        
        print("\n📝 Step 2: Setting up module override...")
        
        # Create a module override file
        override_code = """
import sys
try:
    import pysqlite3
    sys.modules['sqlite3'] = pysqlite3
except ImportError:
    pass  # Fall back to standard sqlite3
"""
        
        with open("_sqlite3_override.py", "w") as f:
            f.write(override_code)
        
        print("✅ Created _sqlite3_override.py")
        
        print("\n🗄️  Step 3: Testing database connection...")
        
        # Test connection
        test_code = """
import _sqlite3_override
import sqlite3

conn = sqlite3.connect('test_replit.db')
conn.execute('CREATE TABLE test (id INTEGER PRIMARY KEY)')
conn.execute('INSERT INTO test VALUES (1)')
conn.commit()
conn.close()
print("✅ Database test successful!")
"""
        
        result = subprocess.run(
            [sys.executable, "-c", test_code],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        if result.returncode == 0:
            print(result.stdout)
            print("\n🎉 Ready to use! Update your imports to add this at the top:")
            print("   import _sqlite3_override")
            return True
        else:
            print(f"❌ Test failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = install_and_setup()
    sys.exit(0 if success else 1)
