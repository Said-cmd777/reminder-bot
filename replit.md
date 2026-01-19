# Telegram Homework Reminder Bot

## Overview
A Telegram bot for managing homework reminders. Users can add, view, and get notified about homework assignments. The bot uses SQLite for persistent storage and APScheduler for scheduled reminders.

## Project Structure
- `bot.py` - Main entry point, Flask keep-alive server, and bot polling
- `config.py` - Configuration from environment variables
- `handlers.py` - Telegram command handlers
- `scheduler.py` - APScheduler manager for reminders
- `db.py` - Database operations with SQLite
- `weekly_schedule.py` - Weekly schedule management

## Environment Variables Required
- `BOT_TOKEN` (required) - Telegram Bot API token from @BotFather
- `ADMIN_IDS` (optional) - Comma-separated Telegram user IDs for admin access

## Running the Bot
The bot runs via `python bot.py` which:
1. Starts a Flask keep-alive server on port 5000
2. Initializes SQLite database
3. Starts the APScheduler for reminders
4. Begins Telegram polling

## Database
Uses SQLite stored at `~/.local/share/reminders.db` on Replit for persistence.

## Deployment
For production deployment, use:
- Command: `python bot.py`
- Type: VM (always-on for bot polling)
