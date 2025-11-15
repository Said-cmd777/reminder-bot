
"""Main entry point for the Telegram Homework Reminder Bot."""
import sys
import signal
import traceback
import os
import telebot

from config import BOT_TOKEN, DB_PATH, BACKUP_DIR, LOG_FILE
from utils import init_logging
from db import get_conn, ensure_tables
from scheduler import SchedulerManager

# ============================================
# Keep-Alive for Replit
# ============================================
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "🤖 Homework Bot is alive!"

def run_flask():
    try:
        app.run(host='0.0.0.0', port=8080)
    except Exception as e:
        print(f"Flask error: {e}")

def keep_alive():
    """Start Flask server in background thread"""
    t = Thread(target=run_flask, daemon=True)
    t.start()
    print("✅ Keep-Alive server started on port 8080")


import importlib.util

handlers_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'handlers.py')
if not os.path.exists(handlers_path):
    raise FileNotFoundError(f"handlers.py not found at {handlers_path}")

spec = importlib.util.spec_from_file_location("handlers", handlers_path)
handlers_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(handlers_module)

import sys
sys.modules["handlers"] = handlers_module
register_handlers = handlers_module.register_handlers


logger = init_logging(LOG_FILE)
logger.info("Starting bot.py")

bot = telebot.TeleBot(BOT_TOKEN)


conn = None
sch_mgr = None


def shutdown_gracefully(signum=None, frame=None, exit_code=0):
    """
    إغلاق البوت بشكل منظم وإغلاق جميع الموارد.
    
    Args:
        signum: رقم الإشارة (إذا تم استدعاؤها من signal handler)
        frame: إطار التنفيذ الحالي
        exit_code: كود الخروج (0 = نجاح، 1 = فشل)
    """
    try:
        signal_name = signal.Signals(signum).name if signum else "Manual"
    except (ValueError, AttributeError):
        
        signal_name = f"Signal {signum}" if signum else "Manual"
    logger.info(f"Received {signal_name}, shutting down gracefully...")
    
    try:
        
        logger.info("Stopping bot polling...")
        bot.stop_polling()
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
    
    try:
        
        if conn:
            logger.info("Closing database connection...")
            conn.close()
            logger.info("Database connection closed.")
    except Exception as e:
        logger.error(f"Error closing database: {e}")
    
    try:
        
        if sch_mgr and hasattr(sch_mgr, 'scheduler'):
            logger.info("Shutting down scheduler...")
            sch_mgr.scheduler.shutdown(wait=True)
            logger.info("Scheduler stopped.")
    except Exception as e:
        logger.error(f"Error shutting down scheduler: {e}")
    
    if exit_code == 0:
        logger.info("Bot stopped gracefully.")
    else:
        logger.error(f"Bot stopped with error (exit code {exit_code})")
    
    sys.exit(exit_code)


def print_startup_banner():
    """طباعة رسالة بداية احترافية."""
    from datetime import datetime
    try:
        from pytz import timezone
        algiers_tz = timezone('Africa/Algiers')
        current_time = datetime.now(algiers_tz)
        time_str = current_time.strftime('%Y-%m-%d %H:%M:%S %Z')
        tz_str = "Africa/Algiers"
    except Exception as e:
        logger.warning(f"Could not load timezone: {e}")
        current_time = datetime.now()
        time_str = current_time.strftime('%Y-%m-%d %H:%M:%S')
        tz_str = "UTC (default)"
    
    print("=" * 50)
    print("🤖 Telegram Homework Reminder Bot")
    print("=" * 50)
    print("✅ Database: Connected")
    print("✅ Scheduler: Running")
    print("✅ Handlers: Registered")
    print(f"🌍 Timezone: {tz_str}")
    print(f"⏰ Current Time: {time_str}")
    print("📡 Status: Polling...")
    print("💡 Press Ctrl+C to stop")
    print("=" * 50)



if __name__ == "__main__":
    try:
        
        try:
            signal.signal(signal.SIGINT, shutdown_gracefully)
            
            if hasattr(signal, 'SIGTERM'):
                signal.signal(signal.SIGTERM, shutdown_gracefully)
        except (ValueError, OSError) as e:
            logger.warning(f"Could not register signal handlers: {e}")
        
        
        # Start Keep-Alive
        keep_alive()
        
        # Database
        logger.info("Initializing database...")
        conn = get_conn(DB_PATH)
        ensure_tables(conn)
        logger.info("Database connection ready.")
        
        # Scheduler
        logger.info("Initializing scheduler...")
        sch_mgr = SchedulerManager(
            bot=bot,
            db_path=DB_PATH,
            backup_dir=BACKUP_DIR,
            use_persistent_jobstore=False
        )
        sch_mgr.bootstrap_all()
        logger.info("Scheduler initialized and started.")
        
        # Handlers
        logger.info("Registering handlers...")
        register_handlers(bot, sch_mgr)
        logger.info("Handlers registered.")
        
        # Banner
        print_startup_banner()
        logger.info("Bootstrap completed — entering polling.")
        
        
        try:
            bot.infinity_polling()
        except telebot.apihelper.ApiTelegramException as e:
            if e.error_code == 409:
                error_msg = """
==================================================
❌ خطأ: تعارض في البوت
==================================================
⚠️  هناك نسخة أخرى من البوت تعمل حالياً!

الخطأ 409 يعني أن هناك بوت آخر يستخدم نفس BOT_TOKEN.

✅ الحل:
1. أوقف البوت على Replit (إذا كان يعمل هناك)
2. أوقف أي نسخة محلية أخرى (Ctrl+C)
3. شغّل نسخة واحدة فقط

==================================================
"""
                print(error_msg)
                logger.error("Bot conflict detected (409 error). Another bot instance is running.")
                logger.error("Please stop all other bot instances before starting this one.")
                shutdown_gracefully(exit_code=1)
            else:
                raise
        
    except KeyboardInterrupt:
        
        logger.info("KeyboardInterrupt received.")
        shutdown_gracefully()
        
    except Exception as e:
        logger.exception("Fatal error in main loop")
        traceback.print_exc()
        
        
        shutdown_gracefully(exit_code=1)
        
    finally:
        
        if conn:
            try:
                conn.close()
                logger.info("Database closed in finally block.")
            except Exception:
                pass
        if sch_mgr and hasattr(sch_mgr, 'scheduler'):
            try:
                sch_mgr.scheduler.shutdown(wait=False)
                logger.info("Scheduler stopped in finally block.")
            except Exception:
                pass
