# bot.py — النسخة المتكاملة التي تربط config, utils, db, scheduler, handlers
"""Main entry point for the Telegram Homework Reminder Bot."""
import sys
import signal
import traceback
import telebot

from config import BOT_TOKEN, DB_PATH, BACKUP_DIR, LOG_FILE
from utils import init_logging
from db import get_conn, ensure_tables
from scheduler import SchedulerManager
# Import from handlers.py directly using importlib
# This ensures we load handlers.py as a file, not as a package
import importlib.util
import os

handlers_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'handlers.py')
if not os.path.exists(handlers_path):
    raise FileNotFoundError(f"handlers.py not found at {handlers_path}")

spec = importlib.util.spec_from_file_location("handlers", handlers_path)
handlers_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(handlers_module)
# Register the module in sys.modules so APScheduler can find it
import sys
sys.modules["handlers"] = handlers_module
register_handlers = handlers_module.register_handlers

# تهيئة البوت واللوجر
logger = init_logging(LOG_FILE)
logger.info("Starting bot.py")

bot = telebot.TeleBot(BOT_TOKEN)

# متغيرات عامة للموارد (سيتم تنظيفها عند الإغلاق)
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
        # على Windows قد لا تكون جميع الإشارات متاحة
        signal_name = f"Signal {signum}" if signum else "Manual"
    logger.info(f"Received {signal_name}, shutting down gracefully...")
    
    try:
        # إيقاف البوت
        logger.info("Stopping bot polling...")
        bot.stop_polling()
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
    
    try:
        # إغلاق قاعدة البيانات
        if conn:
            logger.info("Closing database connection...")
            conn.close()
            logger.info("Database connection closed.")
    except Exception as e:
        logger.error(f"Error closing database: {e}")
    
    try:
        # إيقاف الـ scheduler
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
    print("=" * 50)
    print("🤖 Telegram Homework Reminder Bot")
    print("=" * 50)
    print("✅ Database: Connected")
    print("✅ Scheduler: Running")
    print("✅ Handlers: Registered")
    print("📡 Status: Polling...")
    print("💡 Press Ctrl+C to stop")
    print("=" * 50)


# بدء التشغيل (polling)
if __name__ == "__main__":
    try:
        # تسجيل معالجات الإشارات للإغلاق المنظم
        try:
            signal.signal(signal.SIGINT, shutdown_gracefully)
            # SIGTERM قد لا يكون متاحاً على Windows
            if hasattr(signal, 'SIGTERM'):
                signal.signal(signal.SIGTERM, shutdown_gracefully)
        except (ValueError, OSError) as e:
            logger.warning(f"Could not register signal handlers: {e}")
        
        # تهيئة قاعدة البيانات
        logger.info("Initializing database...")
        conn = get_conn(DB_PATH)
        ensure_tables(conn)
        logger.info("Database connection ready.")
        
        # تهيئة SchedulerManager (يدير جدولة التذكيرات والنسخ الاحتياطي)
        logger.info("Initializing scheduler...")
        sch_mgr = SchedulerManager(
            bot=bot,
            db_path=DB_PATH,
            backup_dir=BACKUP_DIR,
            use_persistent_jobstore=False
        )
        # جدولة كافة التذكيرات الموجودة وجدولة النسخ الاحتياطي
        sch_mgr.bootstrap_all()
        logger.info("Scheduler initialized and started.")
        
        # تسجيل المعالجات (handlers) مع تمرير bot, conn, sch_mgr
        logger.info("Registering handlers...")
        register_handlers(bot, sch_mgr)
        logger.info("Handlers registered.")
        
        # طباعة رسالة البداية
        print_startup_banner()
        logger.info("Bootstrap completed — entering polling.")
        
        # بدء الاستماع للرسائل
        bot.infinity_polling()
        
    except KeyboardInterrupt:
        # تم التعامل معه في signal handler، لكن نضيف fallback
        logger.info("KeyboardInterrupt received.")
        shutdown_gracefully()
        
    except Exception as e:
        logger.exception("Fatal error in main loop")
        traceback.print_exc()
        # في حالة الخطأ، نخرج مع code 1 للإشارة إلى الفشل
        # service manager سيعيد التشغيل تلقائياً
        shutdown_gracefully(exit_code=1)
        
    finally:
        # تنظيف إضافي في حالة عدم استدعاء shutdown_gracefully
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
