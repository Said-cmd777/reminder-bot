# Copilot / AI Agent Instructions for homework-reminder-bot

This document captures the essential knowledge an AI coding agent needs to be productive in this repository.

Summary
- Primary entry: `bot.py` — boots the Telegram bot, starts the scheduler and registers handlers.
- Scheduler: `scheduler.py` — `SchedulerManager` uses APScheduler. job ids follow `hw-{hw_id}-{days}` and `custom_reminder-{id}`.
- Database: `db.py` (SQLite, WAL mode); connection factory `get_conn()` and many helpers live here.
- Handlers: `handlers.py` is the main handlers file (loaded dynamically). The structured handler helpers live under `bot_handlers/`.

Run & developer commands
- Run bot locally: `python bot.py` (or set environment variables and run `python bot.py`). See `README_ENV.md` for env vars examples.
- Recommended environment variables: `BOT_TOKEN` (required), `ADMIN_IDS` (strongly recommended).
- Run tests: `pytest` (project contains `test_*.py` files).

Big-picture architecture and data flow
- `bot.py` creates a `telebot.TeleBot` and a `SchedulerManager`, then calls `register_handlers(bot, sch_mgr)` from `handlers.py`.
- `handlers.py` implements message/callback handlers, uses `db` helpers for persistence and `db_utils.db_connection()` for scoped DB access.
- `SchedulerManager` schedules jobs by adding callable references (string refs like `scheduler:send_hw_reminder`) and expects module-level wrapper functions to be importable by name.
- Jobs and reminders read from `homeworks` and `custom_reminders` tables. Scheduler sends messages using a global `scheduler_bot` reference.

Project-specific conventions & patterns
- Dynamic handler loading: `bot.py` imports `handlers.py` via `importlib.util.spec_from_file_location` and exposes `register_handlers`. Edits to `handlers.py` take effect without package imports — preserve module-level names used by scheduler job refs.
- Job callable refs: scheduler sometimes uses string refs `"module:function"` passed to APScheduler (see `scheduler.py` and `handlers.py`). When adding scheduled callables, provide a module-level function (not a nested closure).
- Job id naming: use `hw-{hw_id}-{days}` for homework reminders and `custom_reminder-{id}` for custom reminders. This convention is used by `SchedulerManager.remove_hw_jobs`.
- DB access: prefer `db_utils.db_connection()` context manager or `get_conn()`; `get_conn()` uses `check_same_thread=False` for multi-thread safety.
- Timezones: repository prefers `Africa/Algiers` when `pytz` is available; code handles absence of `pytz` gracefully.

Important files to inspect for modifications
- `bot.py` — bootstrap, keep-alive (Flask) for Replit, graceful shutdown logic in `shutdown_gracefully()`.
- `scheduler.py` — scheduling rules, jobstore selection (Memory vs SQLAlchemy jobstore), timezone handling.
- `db.py` — schema creation (`ensure_tables`) and data access patterns (uses sqlite3.Row frequently).
- `handlers.py` and `bot_handlers/` — user-facing logic and helper functions (key place for feature work).
- `config.py` — environment-driven configuration. `validate_config()` is run at import and will raise on missing required settings.
- `init_schedule_db.py`, `init_group*_schedule.py` — useful scripts for initializing schedule data.

Debugging and common developer workflows
- To reproduce locally: create `.env` or set `BOT_TOKEN` and `ADMIN_IDS` env vars, then `python bot.py`.
- Logs: defaults to `bot.log` — set `LOG_LEVEL`/`LOG_FILE` in env or `.env`.
- Tests: run `pytest -q` from repository root.
- Stopping: process should be stopped with Ctrl+C to let `shutdown_gracefully()` close DB and scheduler.

What to watch out for (pitfalls)
- `ADMIN_IDS` missing: `config.py` allows running but warns — many admin handlers assume this list exists.
- APScheduler callable references must be importable strings or module-level callables; using lambdas/closures will break scheduled jobs.
- Database migrations: schema is created/updated on startup (`ensure_tables`) — be careful when altering column names (code often checks for column existence).
- Concurrency: code uses SQLite with WAL and `check_same_thread=False`, but still relies on proper `db_connection()` usage to avoid mixed cursors across threads.

Examples (small snippets)
- Schedule a homework reminder job id: `job_id = f"hw-{hw_id}-{days_before}"` (see `scheduler.py`).
- Scheduler callable string example: `callable_ref = f"{__name__}:send_hw_reminder"` and `add_job(callable_ref, 'date', run_date=run_dt, args=[...])`.
- DB connection example: `with db_utils.db_connection() as conn: ...` or `conn = get_conn(DB_PATH)`.

When editing code for features or tests
- Preserve existing job id and callable_ref formats unless you update all places that schedule/remove jobs.
- If you change a DB schema, update `ensure_tables()` in `db.py` and any migration/init scripts under root.
- Prefer adding module-level wrapper functions if you need APScheduler to call into new logic.

If anything here is unclear or you want a shorter or more detailed version, tell me which sections to expand or correct.
