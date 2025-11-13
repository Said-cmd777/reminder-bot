# config.py
"""Configuration settings loaded from environment variables."""
import os
import sys
import logging
import tempfile
from pathlib import Path
from typing import List

# تهيئة logger أولاً
logger = logging.getLogger(__name__)

# محاولة تحميل python-dotenv إذا كان متوفراً (لقراءة ملف .env)
try:
    from dotenv import load_dotenv
    # تحديد المسار الصحيح لملف .env (في نفس مجلد config.py)
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    # تحميل متغيرات البيئة من ملف .env
    if load_dotenv(dotenv_path=env_path):
        logger.info(f"✅ تم تحميل ملف .env من: {env_path}")
    else:
        # محاولة تحميل من المجلد الحالي أيضاً
        if load_dotenv():
            logger.info("✅ تم تحميل ملف .env من المجلد الحالي")
        else:
            logger.warning("⚠️ ملف .env غير موجود - سيتم استخدام متغيرات البيئة العادية")
except ImportError:
    # python-dotenv غير مثبت - لا مشكلة، سنستخدم متغيرات البيئة العادية
    logger.warning("⚠️ python-dotenv غير مثبت - سيتم استخدام متغيرات البيئة العادية فقط")
    logger.warning("💡 لتثبيته: pip install python-dotenv")

# ============================================
# BOT_TOKEN - مطلوب
# ============================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError(
        "BOT_TOKEN غير موجود في متغيرات البيئة. "
        "يرجى تعيينه باستخدام: export BOT_TOKEN='your_token_here' "
        "أو إنشاء ملف .env"
    )

if len(BOT_TOKEN) < 20:
    logger.warning("BOT_TOKEN يبدو قصيراً جداً - تأكد من صحته")

# ============================================
# ADMIN_IDS - مطلوب للأمان
# ============================================
ADMIN_IDS_ENV = os.getenv("ADMIN_IDS")
if ADMIN_IDS_ENV:
    try:
        ADMIN_IDS = [int(uid.strip()) for uid in ADMIN_IDS_ENV.split(",") if uid.strip()]
        if not ADMIN_IDS:
            raise ValueError("ADMIN_IDS فارغ بعد التحليل")
        logger.info(f"✅ تم تحميل {len(ADMIN_IDS)} معرف أدمن من متغيرات البيئة")
    except ValueError as e:
        logger.error(f"خطأ في تحليل ADMIN_IDS: {e}")
        raise ValueError(f"ADMIN_IDS غير صحيح. يجب أن يكون أرقام مفصولة بفواصل. مثال: 123456789,987654321")
else:
    # تحذير أمني واضح جداً
    logger.critical(
        "⚠️ تحذير أمني: ADMIN_IDS غير معيّن! "
        "البوت يعمل في وضع التطوير بدون حماية."
    )
    print("\n" + "="*70)
    print("⚠️  تحذير أمني: لا يوجد ADMIN_IDS معيّن!")
    print("="*70)
    print("للاستخدام في الإنتاج، عيّن ADMIN_IDS في .env:")
    print("  ADMIN_IDS=123456789,987654321")
    print("="*70)
    print("البوت سيعمل بدون حماية - أي شخص يمكنه إضافة/حذف واجبات!")
    print("="*70 + "\n")
    
    ADMIN_IDS = []

# ============================================
# Database & Storage
# ============================================
DB_PATH = os.getenv("DB_PATH", "reminders.db")
BACKUP_DIR = os.getenv("BACKUP_DIR") or "backups"

# التحقق من صحة المسارات وإنشاء المجلدات
db_dir = os.path.dirname(DB_PATH) or "."
if db_dir and not os.path.exists(db_dir):
    try:
        os.makedirs(db_dir, exist_ok=True)
        logger.info(f"✅ تم إنشاء مجلد قاعدة البيانات: {db_dir}")
    except OSError as e:
        raise ValueError(f"لا يمكن إنشاء مجلد قاعدة البيانات {db_dir}: {e}")

# إنشاء مجلد النسخ الاحتياطي
try:
    os.makedirs(BACKUP_DIR, exist_ok=True)
    logger.info(f"✅ مجلد النسخ الاحتياطي: {BACKUP_DIR}")
except OSError as e:
    logger.error(f"❌ لا يمكن إنشاء مجلد النسخ الاحتياطي: {e}")
    BACKUP_DIR = tempfile.gettempdir()
    logger.warning(f"⚠️ استخدام مجلد مؤقت للنسخ الاحتياطي: {BACKUP_DIR}")

# ============================================
# SCHEDULES_DIR - مجلد ملفات PDF للجداول الأسبوعية
# ============================================
SCHEDULES_DIR = os.getenv("SCHEDULES_DIR") or "schedules"
# إنشاء مجلد الجداول إذا لم يكن موجوداً
try:
    os.makedirs(SCHEDULES_DIR, exist_ok=True)
    logger.info(f"✅ مجلد الجداول الأسبوعية: {SCHEDULES_DIR}")
except OSError as e:
    logger.error(f"❌ لا يمكن إنشاء مجلد الجداول {SCHEDULES_DIR}: {e}")
    SCHEDULES_DIR = None
    logger.warning("⚠️ سيتم تعطيل إرسال ملفات PDF للجداول الأسبوعية")

# ============================================
# Logging
# ============================================
LOG_FILE = os.getenv("LOG_FILE") or "bot.log"
LOG_LEVEL = os.getenv("LOG_LEVEL") or "INFO".upper()
LOG_MAX_SIZE = int(os.getenv("LOG_MAX_SIZE") or "10485760")  # 10MB افتراضي

# ============================================
# Telegram API Settings
# ============================================
API_TIMEOUT = int(os.getenv("API_TIMEOUT") or "30")
MAX_RETRIES = int(os.getenv("MAX_RETRIES") or "3")

# ============================================
# Reminder Settings
# ============================================
DEFAULT_REMINDERS = os.getenv("DEFAULT_REMINDERS", "3,2,1")

# ============================================
# Backup Settings
# ============================================
BACKUP_ENABLED = (os.getenv("BACKUP_ENABLED") or "true").lower() == "true"
BACKUP_INTERVAL_HOURS = int(os.getenv("BACKUP_INTERVAL_HOURS") or "24")
MAX_BACKUP_FILES = int(os.getenv("MAX_BACKUP_FILES") or "7")

# ============================================
# Development Settings
# ============================================
DEBUG_MODE = (os.getenv("DEBUG_MODE") or "false").lower() == "true"


# ============================================
# Validation Functions
# ============================================
def validate_config():
    """التحقق من صحة جميع الإعدادات عند بدء التشغيل"""
    errors = []
    warnings = []
    
    # التحقق من BOT_TOKEN
    if not BOT_TOKEN:
        errors.append("BOT_TOKEN مفقود")
    elif len(BOT_TOKEN) < 20:
        warnings.append("BOT_TOKEN يبدو قصيراً جداً - تأكد من صحته")
    
    # التحقق من ADMIN_IDS
    if not ADMIN_IDS:
        warnings.append("⚠️ لا يوجد ADMIN_IDS معيّن - الوضع غير آمن!")
    
    # التحقق من المسارات
    db_dir = os.path.dirname(DB_PATH) or "."
    if not os.access(db_dir, os.W_OK):
        errors.append(f"❌ لا يمكن الكتابة في مسار قاعدة البيانات: {db_dir}")
    
    if not os.access(BACKUP_DIR, os.W_OK):
        warnings.append(f"⚠️ لا يمكن الكتابة في مجلد النسخ الاحتياطي: {BACKUP_DIR}")
    
    # التحقق من قيم الإعدادات
    if API_TIMEOUT < 1:
        warnings.append("API_TIMEOUT يجب أن يكون أكبر من 0")
    
    if MAX_RETRIES < 0:
        warnings.append("MAX_RETRIES يجب أن يكون أكبر من أو يساوي 0")
    
    if BACKUP_INTERVAL_HOURS < 1:
        warnings.append("BACKUP_INTERVAL_HOURS يجب أن يكون أكبر من 0")
    
    # طباعة التحذيرات
    if warnings:
        logger.warning("="*60)
        logger.warning("⚠️ تحذيرات الإعدادات:")
        for w in warnings:
            logger.warning(f"  - {w}")
        logger.warning("="*60)
    
    # إيقاف التشغيل عند وجود أخطاء
    if errors:
        logger.critical("="*60)
        logger.critical("❌ أخطاء حرجة في الإعدادات:")
        for e in errors:
            logger.critical(f"  - {e}")
        logger.critical("="*60)
        raise ValueError("فشل التحقق من الإعدادات. راجع الأخطاء أعلاه.")
    
    if not warnings:  # فقط إذا لم تكن هناك تحذيرات
        logger.info("✅ تم التحقق من جميع الإعدادات بنجاح")


def print_config(hide_sensitive=True):
    """طباعة الإعدادات الحالية (للتشخيص)"""
    token_display = BOT_TOKEN[:20] + "..." if hide_sensitive and BOT_TOKEN else BOT_TOKEN
    
    print("\n" + "="*70)
    print("⚙️  إعدادات البوت")
    print("="*70)
    print(f"BOT_TOKEN:           {token_display}")
    print(f"ADMIN_IDS:           {ADMIN_IDS if ADMIN_IDS else '⚠️  غير معيّن'}")
    print(f"DB_PATH:             {DB_PATH}")
    print(f"BACKUP_DIR:          {BACKUP_DIR}")
    print(f"LOG_FILE:            {LOG_FILE}")
    print(f"LOG_LEVEL:           {LOG_LEVEL}")
    print(f"API_TIMEOUT:         {API_TIMEOUT}s")
    print(f"MAX_RETRIES:         {MAX_RETRIES}")
    print(f"DEFAULT_REMINDERS:   {DEFAULT_REMINDERS}")
    print(f"BACKUP_ENABLED:      {BACKUP_ENABLED}")
    print(f"BACKUP_INTERVAL:     {BACKUP_INTERVAL_HOURS}h")
    print(f"MAX_BACKUP_FILES:    {MAX_BACKUP_FILES}")
    print(f"DEBUG_MODE:          {DEBUG_MODE}")
    print("="*70 + "\n")


# استدعاء التحقق تلقائياً عند الاستيراد
validate_config()
