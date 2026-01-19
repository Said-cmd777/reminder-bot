# Copilot / AI Agent Instructions for homework-reminder-bot

A Telegram bot for managing homework reminders with scheduled notifications, custom reminders, and weekly schedule tracking.

## Quick Start

**Run locally:** `python bot.py` (requires `.env` file or environment variables)

**Required environment variables:**
- `BOT_TOKEN` (required) — Get from [@BotFather](https://t.me/BotFather)
- `ADMIN_IDS` (strongly recommended) — Comma-separated user IDs, e.g., `123456789,987654321`
- See `README_ENV.md` for full configuration options

**Dependencies:** `pip install -r requirements.txt` (pyTelegramBotAPI, APScheduler, SQLAlchemy, python-dotenv, Flask, pytz)

## Architecture Overview

### Core Components
1. **`bot.py`** — Entry point: initializes bot, scheduler, DB, registers handlers
   - Uses `importlib` to dynamically load `handlers.py` (enables edits without package imports)
   - Includes Flask keep-alive server for Replit hosting (port 8080)
   - Signal handlers for graceful shutdown (SIGINT/SIGTERM)
   
2. **`scheduler.py`** — `SchedulerManager` class manages APScheduler jobs
   - Timezone: `Africa/Algiers` (falls back to UTC if pytz unavailable)
   - Jobstore: SQLAlchemyJobStore (persistent) or MemoryJobStore (fallback)
   - Global `scheduler_bot` reference used by scheduled job functions
   
3. **`db.py`** — SQLite database with WAL mode
   - Factory: `get_conn(db_path=None)` returns connection with `check_same_thread=False`
   - Schema: `ensure_tables(conn)` creates/updates tables on startup
   - Tables: `homeworks`, `users`, `homework_completions`, `custom_reminders`, `custom_reminder_completions`, `weekly_schedules`, etc.
   
4. **`handlers.py`** — Main Telegram handlers (3500+ lines)
   - Registers all message/callback query handlers via `register_handlers(bot, sch_mgr)`
   - Uses `global_bot` reference for APScheduler callable functions
   - Implements multi-step state management for user interactions
   
5. **`bot_handlers/`** — Modular handler helpers
   - `base.py`: `StateManager`, `BotHandlers`, `RateLimiter` classes
   - `helpers.py`: Keyboard builders, text formatting, admin checks
   - `schedule_admin_helpers.py`: Weekly schedule admin UI
   - `weekly_schedule_helpers.py`: Weekly schedule display logic

### Data Flow
```
bot.py → SchedulerManager.bootstrap_all() → reschedule existing jobs from DB
       → register_handlers() → handlers.py registers all callbacks
       → bot.infinity_polling() → user messages → handlers execute
                                 → handlers call sch_mgr.schedule_homework_reminders()
                                 → jobs fire → send_hw_reminder() → scheduler_bot.send_message()
```

## Critical Patterns & Conventions

### APScheduler Job References
**Problem:** APScheduler requires callable references to be importable by name (not closures/lambdas)

**Solution:** Use module-level functions with string references:
```python
# In scheduler.py or handlers.py (module level)
def send_hw_reminder(hw_id: int, days_before: int, db_path: str):
    global scheduler_bot
    scheduler_bot.send_message(...)

# Schedule it:
callable_ref = f"{__name__}:send_hw_reminder"
sch_mgr.scheduler.add_job(callable_ref, 'date', run_date=dt, args=[hw_id, days, DB_PATH])
```

**Job ID Convention:**
- Homework reminders: `hw-{hw_id}-{days_before}` (e.g., `hw-42-3`)
- Custom reminders: `custom_reminder-{reminder_id}` (e.g., `custom_reminder-17`)
- Used by `SchedulerManager.remove_hw_jobs()` to clean up jobs

### Database Access Patterns
**Prefer context manager for scoped connections:**
```python
from db_utils import db_connection

with db_connection() as conn:
    conn.execute("INSERT INTO homeworks ...")
    # auto-commit on success, rollback on error
```

**Direct connection (for long-lived operations):**
```python
from db import get_conn
conn = get_conn(DB_PATH)  # check_same_thread=False for multi-threading
conn.close()  # remember to close!
```

**Safe row access:**
```python
from db_utils import safe_get
subject = safe_get(row, 'subject', default='Unknown', warn=True)
```

### State Management
Handlers use `StateManager` for multi-step user interactions:
```python
state_mgr = StateManager()
state_mgr.start(chat_id, StateType.ADD_HOMEWORK, initial_data={'step': 1})
state_mgr.update(chat_id, step='subject', subject='Math')
state = state_mgr.get(chat_id)  # Returns UserState or None
state_mgr.clear(chat_id)
```

### Dynamic Handler Loading
`bot.py` uses `importlib.util.spec_from_file_location` to load `handlers.py`:
- Changes to `handlers.py` don't require package reinstall
- Preserve module-level function names used in scheduler string refs
- `sys.modules["handlers"]` is set for compatibility

### Timezone Handling
- Default: `Africa/Algiers` (Algeria timezone)
- Gracefully degrades if `pytz` unavailable (logs warning, uses UTC/system time)
- `SchedulerManager` sets timezone on BackgroundScheduler instance

### Database Schema Evolution
- `ensure_tables()` uses `CREATE TABLE IF NOT EXISTS`
- Check column existence before accessing: many scripts handle old schemas
- Migration scripts in root: `migrate_db.py`, `init_schedule_db.py`, etc.
- WAL mode: `PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;`

## Key Files for Modifications

| File | Purpose | Watch Out For |
|------|---------|---------------|
| `config.py` | Env var loading, validation | Runs at import, raises on missing `BOT_TOKEN` |
| `db.py` | DB helpers, schema | Update `ensure_tables()` for schema changes |
| `handlers.py` | Main handlers | Keep module-level callables for scheduler |
| `scheduler.py` | Job scheduling logic | Job IDs, callable string refs, timezone |
| `bot_handlers/*.py` | Handler utilities | State management, keyboard builders |

## Debugging & Development

**Check scheduler jobs:**
```bash
python check_scheduled_jobs.py
```

**Inspect DB reminders:**
```bash
python check_db_reminders.py
python check_db_status.py
```

**View registered users:**
```bash
python view_users.py
```

**Logs:** Default `bot.log` (configurable via `LOG_FILE` env var)

**Tests:** Run `python test_reminder_scheduling.py` (pytest not fully configured)

**Common 409 error:** Another bot instance is running with same token — stop all instances first

## Pitfalls & Gotchas

1. **ADMIN_IDS unset:** Bot runs but all admin commands are unprotected (logs critical warning)
2. **Scheduler callable closures:** Don't use lambdas — APScheduler can't serialize them
3. **DB schema assumptions:** Code checks for column existence, but assumes `sqlite3.Row` factory
4. **Thread safety:** Use `db_connection()` context manager, not shared cursors
5. **Replit deployment:** Uses persistent DB path `~/.local/share/reminders.db`, Flask keep-alive on port 8080
6. **Signal handlers:** May fail on Windows (`SIGTERM` unavailable) — gracefully handled
7. **Jobstore persistence:** `use_persistent_jobstore=False` in `bot.py` (uses MemoryJobStore) — jobs lost on restart

## Example Workflows

**Add homework with reminders:**
1. User: `/add` → Handler starts `StateType.ADD_HOMEWORK` state
2. Handler prompts for subject, due date, reminders (e.g., `3,1,0`)
3. On complete: `insert_homework()` → `sch_mgr.schedule_homework_reminders(row)`
4. Scheduler adds jobs: `hw-{id}-3`, `hw-{id}-1`, `hw-{id}-0`
5. Jobs fire at calculated times → `send_hw_reminder()` → messages sent

**Custom reminder:**
1. User: `/reminder` → State starts
2. User enters text, datetime → `insert_custom_reminder()`
3. Scheduler adds job: `custom_reminder-{id}` → fires at datetime

**Weekly schedule:**
1. Admin: `/schedule_admin` → view/edit weekly class schedules
2. DB: `weekly_schedules` table (group, day_of_week, time_start, course, location)
3. Users: `/schedule` → view today/tomorrow/week schedules

## When Making Changes

- **New scheduled callable?** Add module-level function, use `f"{__name__}:func_name"` reference
- **DB schema change?** Update `ensure_tables()`, test migration scripts, check column checks
- **New handler?** Register in `register_handlers()`, consider state management
- **Deployment?** Test on Replit (env vars, DB path, keep-alive), check Procfile/logs

For questions or unclear sections, ask about specific components or workflows.
