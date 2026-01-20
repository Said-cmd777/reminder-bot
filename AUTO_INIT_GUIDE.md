# Auto-Initialization System for Schedule Data

## Overview

The bot includes an automatic initialization system that restores weekly schedule data from `schedule_data.sql` when the database is empty or missing. This is critical for cloud platforms with ephemeral storage like Render, Railway, or Fly.io.

## Problem Statement

Cloud platforms often use ephemeral storage, meaning:
- The filesystem is reset on every deployment or restart
- The SQLite database (`reminders.db`) is recreated fresh (empty)
- Schedule data for Groups 02, 03, and 04 is lost
- Users cannot access their weekly schedules

## Solution

The auto-initialization system automatically detects when schedule data is missing and restores it from the `schedule_data.sql` file that's committed to the repository.

## How It Works

### 1. Startup Flow

```
bot.py startup
  ↓
Initialize database (create tables)
  ↓
Check if schedule data exists
  ↓
If missing → Auto-restore from schedule_data.sql
  ↓
Continue with bot initialization
```

### 2. Key Components

#### `auto_init_schedules.py`
Main module containing the auto-initialization logic:

- **`auto_init_schedules(db_path, sql_file)`**: Main entry point
  - Checks if schedule data exists
  - Restores if missing
  - Returns True if data is available

- **`check_schedule_data_exists(db_path)`**: Detection
  - Checks if database file exists
  - Verifies `weekly_schedule_classes` table has data
  - Returns True if data is present

- **`restore_schedule_data(db_path, sql_file)`**: Restoration
  - Parses SQL statements from file
  - Creates required tables if missing
  - Executes INSERT statements
  - Verifies data integrity
  - Returns True if successful

- **`parse_sql_statements(sql_content)`**: SQL Parser
  - Handles multi-line SQL statements
  - Properly manages SQL comments (`--`)
  - Preserves string literals with quotes
  - Splits on semicolons outside strings

#### `bot.py` Integration

The auto-initialization is called during bot startup:

```python
# Database
logger.info("Initializing database...")
conn = get_conn(DB_PATH)
ensure_tables(conn)
logger.info("Database connection ready.")

# Auto-initialize schedule data if needed (critical for cloud platforms)
logger.info("Checking schedule data...")
auto_init_schedules(DB_PATH)
logger.info("Schedule data check completed.")
```

### 3. Idempotent Behavior

The system is **idempotent** - safe to run multiple times:

- ✅ First run: Detects empty database, restores all data
- ✅ Second run: Detects existing data, skips restoration
- ✅ After redeploy: Detects missing data, restores again

This means the bot can restart safely without data duplication or loss.

## What Gets Restored

From `schedule_data.sql`:

1. **Weekly Schedule Classes** (60 total)
   - Group 01: 15 classes
   - Group 02: 15 classes
   - Group 03: 15 classes
   - Group 04: 15 classes

2. **Alternating Week Configuration** (2 entries)
   - algorithm1: Reference date for Algorithm lab sessions
   - statistics1: Reference date for Statistics lab sessions

## Log Output

### Normal Startup (Data Already Exists)
```
Checking schedule data...
🔍 Checking schedule data availability...
Schedule data exists: 60 classes found
✅ Schedule data already present - no restoration needed
Schedule data check completed.
```

### First Startup or After Reset (Data Restored)
```
Checking schedule data...
🔍 Checking schedule data availability...
Database file does not exist: reminders.db
⚠️  Schedule data missing - attempting automatic restoration...
🔄 Starting schedule data restoration from schedule_data.sql
📖 Reading schedule_data.sql...
🔍 Parsing SQL statements...
   Found 64 statements
🗄️  Connecting to reminders.db...
📋 Ensuring database tables exist...
💾 Committing changes...
📊 Verifying restoration...
   📚 Schedule classes: 60
   🔄 Alternating configs: 2
   ✨ Group 01: 15 classes
   ✨ Group 02: 15 classes
   ✨ Group 03: 15 classes
   ✨ Group 04: 15 classes
✅ Schedule data restoration completed!
   Successful statements: 64
✅ Schedule data automatically restored
Schedule data check completed.
```

## Testing

Run the standalone test:

```bash
python3 auto_init_schedules.py [db_path] [sql_file]
```

Example:
```bash
python3 auto_init_schedules.py test.db schedule_data.sql
```

## Cloud Platform Deployment

### Render

1. Deploy your bot to Render
2. On first startup, the database is empty
3. Auto-init detects this and restores schedule data
4. Users can access all group schedules
5. On redeploy, the process repeats automatically

### Railway / Fly.io

Same behavior as Render - the auto-init system works on any platform with ephemeral storage.

### Persistent Storage Platforms

If you're using a platform with persistent storage (like Replit with Always-On):
- First startup: Data is restored
- Subsequent startups: Data persists, restoration is skipped
- Still safe and idempotent

## Troubleshooting

### Issue: Schedule data not restored

**Symptoms:**
- Users report missing schedules for Groups 02, 03, 04
- Logs show "Schedule data check completed" but no restoration

**Solutions:**
1. Check if `schedule_data.sql` exists in the repository
2. Verify the SQL file has correct data (60 classes, 2 configs)
3. Check logs for error messages during restoration
4. Manually test: `python3 auto_init_schedules.py reminders.db schedule_data.sql`

### Issue: Duplicate data

**Symptoms:**
- Multiple copies of the same schedule entries

**Cause:**
- Direct SQL execution bypassing the auto-init system
- Manual imports while data already exists

**Solution:**
- The auto-init system has built-in duplicate detection
- If duplicates exist, delete the database and let auto-init restore cleanly

### Issue: Parser errors

**Symptoms:**
- Logs show "Failed to restore schedule data"
- SQL parsing errors in logs

**Cause:**
- Malformed SQL in `schedule_data.sql`
- Special characters or encoding issues

**Solution:**
1. Verify `schedule_data.sql` syntax is valid
2. Check for unmatched quotes or parentheses
3. Ensure file uses UTF-8 encoding
4. Test parsing: `python3 -c "from auto_init_schedules import parse_sql_statements; ..."`

## Updating Schedule Data

To update the schedule data:

1. Modify `schedule_data.sql` with new/updated schedules
2. Test locally: Delete `reminders.db` and restart bot
3. Verify restoration works correctly
4. Commit and push changes
5. Redeploy - new data will be automatically loaded

## Benefits

✅ **Zero Manual Intervention**: No need to manually restore data after deployments
✅ **Cloud-Ready**: Works on any cloud platform with ephemeral storage
✅ **Idempotent**: Safe to run multiple times, no data duplication
✅ **Fast**: Restoration completes in milliseconds
✅ **Reliable**: Built-in error handling and verification
✅ **Logged**: Clear logging for debugging and monitoring
✅ **Version Controlled**: Schedule data is in Git, easy to update

## Technical Notes

- Uses SQLite3 with WAL mode for optimal performance
- SQL parser handles complex statements with quotes and comments
- Tables are created automatically if missing
- Restoration is atomic (all or nothing)
- No external dependencies beyond Python standard library + sqlite3

## Support

For issues or questions about the auto-initialization system, check:
- This guide
- Code comments in `auto_init_schedules.py`
- Bot startup logs
- GitHub Issues
