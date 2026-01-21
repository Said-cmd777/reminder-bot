# PostgreSQL Support for Reminder Bot

## Overview

The bot now supports both SQLite (for local development) and PostgreSQL (for production deployment on platforms like Render or Heroku). The database type is automatically detected based on the presence of the `DATABASE_URL` environment variable.

## Database Selection

- **SQLite**: Used by default when `DATABASE_URL` is not set. Best for local development.
- **PostgreSQL**: Used automatically when `DATABASE_URL` is set. Best for production deployment.

## Local Development (SQLite)

No additional configuration needed! The bot will use SQLite by default:

```bash
# Just set your bot credentials
export BOT_TOKEN="your_bot_token_here"
export ADMIN_IDS="123456789,987654321"

# Run the bot
python bot.py
```

Data is stored in `reminders.db` (or the path specified in `DB_PATH` environment variable).

## Production Deployment (PostgreSQL)

### Setting up PostgreSQL on Render

1. **Create a PostgreSQL Database:**
   - Log in to your [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" → "PostgreSQL"
   - Configure your database:
     - **Name**: Choose a name (e.g., `reminder-bot-db`)
     - **Database**: Leave as default or customize
     - **User**: Leave as default or customize
     - **Region**: Select a region close to your web service
     - **PostgreSQL Version**: Use the latest stable version
     - **Plan**: Select Free or paid plan based on your needs
   - Click "Create Database"

2. **Get the Database Connection String:**
   - Once created, go to your database's dashboard
   - Under "Connections", you'll see:
     - **Internal Database URL** (recommended for Render services)
     - **External Database URL** (for external connections)
   - Copy the **Internal Database URL** (it looks like this):
     ```
     postgresql://user:password@dpg-xxxxx-internal.oregon-postgres.render.com/dbname
     ```

3. **Configure Your Web Service:**
   - Go to your web service (the bot) in Render dashboard
   - Navigate to "Environment" section
   - Add a new environment variable:
     - **Key**: `DATABASE_URL`
     - **Value**: Paste the Internal Database URL
   - Click "Save Changes"

4. **Deploy:**
   - Render will automatically redeploy your service
   - The bot will detect `DATABASE_URL` and use PostgreSQL
   - On first run, the bot will automatically create all required tables
   - Your data will now persist across redeployments! 🎉

### Setting up PostgreSQL on Heroku

1. **Add PostgreSQL Add-on:**
   ```bash
   heroku addons:create heroku-postgresql:hobby-dev
   ```

2. **Get Database URL:**
   ```bash
   heroku config:get DATABASE_URL
   ```

3. **Set Environment Variables:**
   ```bash
   heroku config:set BOT_TOKEN="your_bot_token"
   heroku config:set ADMIN_IDS="123456789,987654321"
   ```

4. **Deploy:**
   ```bash
   git push heroku main
   ```

## Environment Variables

### Required
- `BOT_TOKEN`: Your Telegram bot token from [@BotFather](https://t.me/BotFather)
- `ADMIN_IDS`: Comma-separated list of admin user IDs (e.g., `123456789,987654321`)

### Database Configuration
- `DATABASE_URL`: PostgreSQL connection string (format: `postgresql://user:password@host:5432/dbname`)
  - If set → PostgreSQL is used
  - If not set → SQLite is used

### Optional (SQLite only)
- `DB_PATH`: Path to SQLite database file (default: `reminders.db`)
- `BACKUP_DIR`: Directory for backups (default: `backups`)

## Testing PostgreSQL Locally

You can test PostgreSQL locally using Docker:

```bash
# Start PostgreSQL container
docker run --name reminder-db -e POSTGRES_PASSWORD=mysecretpassword -p 5432:5432 -d postgres

# Set DATABASE_URL
export DATABASE_URL="postgresql://postgres:mysecretpassword@localhost:5432/postgres"

# Run the bot
python bot.py
```

## Migration Notes

- **No manual migration needed**: When you switch from SQLite to PostgreSQL, the bot will automatically create all tables on first run
- **Data migration**: If you want to migrate existing data from SQLite to PostgreSQL, you'll need to export and import manually (see below)

### Manual Data Migration (Optional)

If you have existing data in SQLite and want to move it to PostgreSQL:

```bash
# 1. Export SQLite data
sqlite3 reminders.db .dump > dump.sql

# 2. Edit dump.sql to convert SQLite-specific syntax to PostgreSQL
# - Replace AUTOINCREMENT with SERIAL
# - Replace datetime('now') with CURRENT_TIMESTAMP
# - Handle any other SQLite-specific syntax

# 3. Import to PostgreSQL
psql $DATABASE_URL < dump.sql
```

## Schema Compatibility

The bot handles schema differences automatically:

| Feature | SQLite | PostgreSQL |
|---------|--------|------------|
| Auto-increment | `AUTOINCREMENT` | `SERIAL` |
| Current timestamp | `datetime('now')` | `CURRENT_TIMESTAMP` |
| Datetime storage | TEXT | TIMESTAMP |
| Upsert | `INSERT OR REPLACE` | `ON CONFLICT ... DO UPDATE` |
| User IDs | INTEGER | BIGINT |

## Troubleshooting

### Connection Errors

If you see connection errors:
- Verify `DATABASE_URL` is correctly set
- Check that your PostgreSQL database is running
- Ensure your IP is whitelisted (for external connections)

### Missing psycopg2

If you see "psycopg2 not available":
```bash
pip install psycopg2-binary
```

### Table Creation Errors

If tables aren't being created:
- Check database permissions
- Verify the database user has CREATE TABLE privileges
- Check logs for specific error messages

## Support

For issues or questions:
- Check logs: The bot logs database type detection on startup
- Open an issue on GitHub
- Consult Render documentation: https://render.com/docs/databases
