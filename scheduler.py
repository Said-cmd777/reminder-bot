
"""
Scheduler manager — يدير جدولة التذكيرات والنسخ الاحتياطي بطريقة مستديمة (SQLAlchemyJobStore) أو ذاكرة.
أُضيف هنا معامل use_persistent_jobstore ليتوافق مع ما قد يمرره bot.py.
"""

import os
import shutil
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError
from apscheduler.jobstores.memory import MemoryJobStore

# Import database adapter
from db import get_conn
from db_adapter import close_conn
from db_config import DB_TYPE

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# استيراد pytz
try:
    from pytz import timezone as pytz_timezone
    PYTZ_AVAILABLE = True
except ImportError:
    PYTZ_AVAILABLE = False
    logger.warning("pytz غير متاح - سيتم استخدام UTC")

# جعل SQLAlchemyJobStore اختياري - إذا لم يكن متاحاً، سنستخدم MemoryJobStore
try:
    from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    logger.warning("SQLAlchemy غير متاح - سيتم استخدام MemoryJobStore بدلاً من SQLAlchemyJobStore")

scheduler_bot = None  # سيعيّن عند تهيئة SchedulerManager

# استيراد get_notification_setting في أعلى الملف لتجنب مشاكل الاستيراد داخل الدالة
try:
    from db import get_notification_setting
    NOTIFICATION_SETTING_AVAILABLE = True
except ImportError:
    NOTIFICATION_SETTING_AVAILABLE = False
    logger.warning("get_notification_setting غير متاح - سيتم إرسال التذكيرات بدون فحص الإعدادات")

def send_hw_reminder(hw_id: int, days_before: int, db_path: str):
    global scheduler_bot
    try:
        conn = get_conn(db_path)
        cur = conn.cursor()
        
        placeholder = "%s" if DB_TYPE == "postgresql" else "?"
        
        if DB_TYPE == "postgresql":
            import psycopg2.extras
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(f"SELECT * FROM homeworks WHERE id = {placeholder}", (hw_id,))
        else:
            conn.row_factory = sqlite3.Row
            cur.execute(f"SELECT * FROM homeworks WHERE id = {placeholder}", (hw_id,))
        
        row = cur.fetchone()
        if not row:
            close_conn(conn)
            logger.info("send_hw_reminder: no row for hw_id=%s", hw_id)
            return
        

        subject = row['subject']
        due_at = row['due_at']
        description = row['description'] or ""
        conditions = row['conditions'] or "-"
        pdf_type = row['pdf_type']
        pdf_value = row['pdf_value']
        target_chat = row['chat_id']
        target_user = None
        try:
            target_user_val = row['target_user_id']
            
            if target_user_val is not None:
                target_user = int(target_user_val)
        except (KeyError, TypeError, ValueError):
            target_user = None

        text = (f"⏰ تذكير قبل {days_before} يوم/أيام من موعد الواجب\n"
                f"المادة: {subject}\n"
                f"الموعد: {due_at}\n"
                f"الوصف: {description}\n"
                f"الشروط: {conditions}\n"
                f"ID: {hw_id}")

        
        
        if target_user is not None:
            recipients = [target_user]
            logger.info("send_hw_reminder: sending to specific user_id=%s", target_user)
        else:
            
            try:
                cur.execute("SELECT user_id FROM users")
                user_rows = cur.fetchall()
                recipients = [r[0] if isinstance(r, tuple) else r['user_id'] for r in user_rows if (r[0] if isinstance(r, tuple) else r['user_id']) is not None]
                if not recipients:
                    
                    logger.warning("send_hw_reminder: no registered users found, sending to chat_id=%s", target_chat)
                    recipients = [target_chat]
                else:
                    logger.info("send_hw_reminder: sending to %d registered users (all users)", len(recipients))
            except Exception as e:
                logger.exception("send_hw_reminder: failed to get registered users, falling back to chat_id")
                recipients = [target_chat]

        for recip in recipients:
            try:
                if scheduler_bot is None:
                    logger.error("send_hw_reminder: scheduler_bot غير مضبوط — لا أستطيع الإرسال")
                    continue
                
                
                
                if isinstance(recip, int) and recip > 0:  
                    placeholder = "%s" if DB_TYPE == "postgresql" else "?"
                    cur.execute(f"SELECT 1 FROM homework_completions WHERE hw_id = {placeholder} AND user_id = {placeholder}", (hw_id, recip))
                    if cur.fetchone() is not None:
                        logger.info("send_hw_reminder: user_id=%s already completed hw_id=%s, skipping", recip, hw_id)
                        continue
                    
                    # فحص إعدادات الإشعارات
                    if NOTIFICATION_SETTING_AVAILABLE:
                        try:
                            if not get_notification_setting(conn, recip, 'homework_reminders'):
                                logger.info("send_hw_reminder: user_id=%s disabled homework_reminders, skipping", recip)
                                continue
                        except Exception as notif_err:
                            logger.warning("send_hw_reminder: failed to check notification settings for user_id=%s: %s", recip, notif_err)
                            # في حالة الخطأ، نتابع الإرسال (افتراضياً مفعّل)
                    else:
                        logger.debug("send_hw_reminder: notification settings check unavailable, sending anyway")
                        
                
                scheduler_bot.send_message(recip, text)
                if pdf_type == "file_id" and pdf_value:
                    try:
                        scheduler_bot.send_document(recip, pdf_value)
                    except Exception:
                        logger.exception("Failed to send document file_id for hw_id=%s", hw_id)
                elif pdf_type == "url" and pdf_value:
                    try:
                        from telebot import types as _types
                        kb = _types.InlineKeyboardMarkup()
                        kb.add(_types.InlineKeyboardButton("ملف الواجب (رابط)", url=pdf_value))
                        scheduler_bot.send_message(recip, "ملف الواجب:", reply_markup=kb)
                    except Exception:
                        logger.exception("Failed to send pdf url for hw_id=%s", hw_id)
                logger.info("send_hw_reminder: sent hw_id=%s to recip=%s", hw_id, recip)
            except Exception as e:
                logger.exception("send_hw_reminder: failed to send hw_id=%s to recip=%s — %s", hw_id, recip, e)
        close_conn(conn)
    except Exception:
        logger.exception("send_hw_reminder: unexpected error for hw_id=%s", hw_id)


def backup_db_once(db_path: str, backup_dir: str):
    try:
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = os.path.join(backup_dir, f"reminders_backup_{ts}.db")
        shutil.copy2(db_path, dest)
        logger.info("backup_db_once: Database backed up to %s", dest)
    except Exception:
        logger.exception("backup_db_once: failed to backup database")


class SchedulerManager:
    def __init__(self,
                 bot,
                 db_path: str = "reminders.db",
                 backup_dir: str = "backups",
                 jobs_db: str = "jobs.sqlite",
                 use_persistent_jobstore: bool = True):
        """
        bot: telebot.TeleBot instance
        use_persistent_jobstore: إذا True يحاول استخدام SQLAlchemyJobStore
        """
        global scheduler_bot
        scheduler_bot = bot

        self.db_path = db_path
        self.backup_dir = backup_dir
        self.jobs_db = jobs_db
        self.use_persistent_jobstore = bool(use_persistent_jobstore)

        # ============================================
        # Timezone Setup
        # ============================================
        if PYTZ_AVAILABLE:
            try:
                self.timezone = pytz_timezone('Africa/Algiers')
                logger.info("✅ Timezone set to: Africa/Algiers")
            except Exception as e:
                logger.warning(f"Failed to set Algeria timezone: {e}, using UTC")
                self.timezone = pytz_timezone('UTC')
        else:
            self.timezone = None
            logger.warning("⚠️ pytz not available - scheduler will use system timezone")

        # ============================================
        # Jobstore Setup
        # ============================================
        if self.use_persistent_jobstore and SQLALCHEMY_AVAILABLE:
            try:
                url = f"sqlite:///{os.path.abspath(self.jobs_db)}"
                jobstores = {'default': SQLAlchemyJobStore(url=url)}
                logger.info("SchedulerManager: using SQLAlchemyJobStore at %s", self.jobs_db)
            except Exception:
                logger.exception("SchedulerManager: failed to use SQLAlchemyJobStore, falling back to MemoryJobStore")
                jobstores = {'default': MemoryJobStore()}
        else:
            if self.use_persistent_jobstore and not SQLALCHEMY_AVAILABLE:
                logger.warning("SchedulerManager: SQLAlchemy غير متاح - سيتم استخدام MemoryJobStore")
            jobstores = {'default': MemoryJobStore()}

        # ============================================
        # Create Scheduler with Timezone
        # ============================================
        if self.timezone:
            self.scheduler = BackgroundScheduler(
                jobstores=jobstores,
                timezone=self.timezone,  # ← المهم!
                job_defaults={'coalesce': False, 'max_instances': 5}
            )
            logger.info("✅ Scheduler created with timezone: %s", self.timezone)
        else:
            self.scheduler = BackgroundScheduler(
                jobstores=jobstores,
                job_defaults={'coalesce': False, 'max_instances': 5}
            )
            logger.warning("⚠️ Scheduler created without explicit timezone")

        self.scheduler.start()
        logger.info("Scheduler started.")

    def remove_hw_jobs(self, hw_id: int):
        for days in range(0, 366):
            jid = f"hw-{hw_id}-{days}"
            try:
                self.scheduler.remove_job(jid)
            except JobLookupError:
                continue
            except Exception:
                logger.exception("remove_hw_jobs: failed removing job %s", jid)

    def schedule_homework_reminders(self, hw_row):
        try:
            hw_id = hw_row['id']
        except Exception:
            logger.error("schedule_homework_reminders: invalid hw_row, missing id")
            return

        try:
            if hw_row['done'] == 1:
                self.remove_hw_jobs(hw_id)
                logger.info("schedule_homework_reminders: hw_id=%s already done -> removed jobs", hw_id)
                return
        except Exception:
            pass

        try:
            # قراءة due_at من قاعدة البيانات
            due_naive = datetime.strptime(hw_row['due_at'], "%Y-%m-%d %H:%M")
            
            # إضافة timezone إذا كان متاحاً
            if PYTZ_AVAILABLE and hasattr(self, 'timezone') and self.timezone:
                # إذا كان scheduler له timezone، استخدمه لـ localize naive datetime
                try:
                    due = self.timezone.localize(due_naive)
                    logger.debug("schedule_homework_reminders: localized due_at to timezone %s: %s", self.timezone, due)
                except Exception as tz_err:
                    # إذا فشل localize، استخدم naive datetime
                    logger.warning("schedule_homework_reminders: failed to localize due_at: %s, using naive datetime", tz_err)
                    due = due_naive
            else:
                # بدون timezone - naive datetime
                due = due_naive
                logger.debug("schedule_homework_reminders: using naive datetime (no timezone available)")
        except Exception:
            logger.exception("schedule_homework_reminders: invalid due_at for hw_id=%s", hw_id)
            return

        remind_spec = None
        try:
            # دعم sqlite3.Row و dict - استخدام safe_get من db_utils
            from db_utils import safe_get
            remind_spec = safe_get(hw_row, 'reminders', None)
            
            # معالجة حالات None و 'None' (string) و ''
            if remind_spec is None:
                remind_spec = None
            elif isinstance(remind_spec, str):
                remind_spec = remind_spec.strip()
                if remind_spec.lower() in ('none', 'null', ''):
                    remind_spec = None
        except Exception as e:
            logger.warning("schedule_homework_reminders: failed to get reminders for hw_id=%s: %s", hw_id, e)
            remind_spec = None
        
        # تسجيل تفصيلي للتشخيص
        logger.debug("schedule_homework_reminders: hw_id=%s, remind_spec raw=%s, type=%s", 
                    hw_id, repr(remind_spec), type(remind_spec).__name__)

        logger.info("schedule_homework_reminders: hw_id=%s, remind_spec='%s'", hw_id, remind_spec)

        if not remind_spec:
            remind_spec = "3,2,1"
            logger.debug("schedule_homework_reminders: using default reminders for hw_id=%s", hw_id)

        offsets = []
        for part in str(remind_spec).split(","):
            p = part.strip()
            if not p:
                continue
            try:
                v = int(p)
                if 0 <= v <= 3650:
                    offsets.append(v)
                    logger.debug("schedule_homework_reminders: added offset %s for hw_id=%s", v, hw_id)
            except Exception:
                logger.warning("schedule_homework_reminders: failed to parse reminder offset '%s' for hw_id=%s", p, hw_id)
                continue
        if not offsets:
            offsets = [3, 2, 1]
            logger.debug("schedule_homework_reminders: no valid offsets, using default [3,2,1] for hw_id=%s", hw_id)
        
        logger.info("schedule_homework_reminders: hw_id=%s, final offsets=%s", hw_id, offsets)

        # الحصول على الوقت الحالي مع نفس timezone الخاص بـ due
        if PYTZ_AVAILABLE and hasattr(self, 'timezone') and self.timezone:
            # إذا كان due timezone-aware، استخدم نفس timezone للوقت الحالي
            now = datetime.now(self.timezone)
            logger.info("Current Time (Algiers): %s", now)
            logger.debug("schedule_homework_reminders: using timezone-aware datetime for now: %s", now)
        else:
            # بدون timezone - naive datetime
            now = datetime.now()
            logger.debug("schedule_homework_reminders: using naive datetime for now: %s", now)
        
        logger.debug("schedule_homework_reminders: hw_id=%s, due=%s, now=%s", hw_id, due, now)
        
        for days_before in offsets:
            try:
                run_dt = due - timedelta(days=days_before)
            except Exception:
                logger.exception("schedule_homework_reminders: invalid timedelta for hw_id=%s days_before=%s", hw_id, days_before)
                continue

            # التعامل مع التذكيرات الفورية (days_before=0) والتذكيرات في الماضي
            time_diff = (run_dt - now).total_seconds()
            
            logger.debug("schedule_homework_reminders: hw_id=%s, days_before=%s, run_dt=%s, time_diff=%s seconds", 
                        hw_id, days_before, run_dt, time_diff)
            
            if days_before == 0:
                # للتذكيرات الفورية (0 أيام): أرسل فوراً إذا كان الموعد في الماضي أو الآن
                if time_diff <= 0:
                    logger.info("schedule_homework_reminders: sending immediate reminder (days_before=0) for hw_id=%s (due was %s, now is %s, diff=%s seconds)", 
                               hw_id, due, now, time_diff)
                    # إرسال التذكير مباشرة بدلاً من جدولته
                    logger.debug("schedule_homework_reminders: calling send_hw_reminder directly for hw_id=%s", hw_id)
                    try:
                        # التحقق من أن scheduler_bot مضبوط
                        if scheduler_bot is None:
                            logger.error("schedule_homework_reminders: scheduler_bot is None, cannot send immediate reminder for hw_id=%s", hw_id)
                        else:
                            logger.debug("schedule_homework_reminders: scheduler_bot is set, calling send_hw_reminder for hw_id=%s", hw_id)
                            send_hw_reminder(hw_id, days_before, self.db_path)
                            logger.info("schedule_homework_reminders: successfully sent immediate reminder for hw_id=%s", hw_id)
                    except Exception as e:
                        logger.exception("schedule_homework_reminders: failed to send immediate reminder for hw_id=%s: %s", hw_id, e)
                    # لا نحتاج لجدولة التذكير لأنه تم إرساله فوراً
                    continue
                # إذا كان الموعد في المستقبل، استمر في جدولة التذكير في وقت الموعد
            else:
                # للتذكيرات الأخرى (days_before > 0): تخطّ إذا كانت في الماضي
                if time_diff < 0:
                    logger.debug("schedule_homework_reminders: skipping past reminder for hw_id=%s days_before=%s (run_dt=%s, diff=%s seconds)", 
                                hw_id, days_before, run_dt, time_diff)
                    continue

            # جدولة التذكير في وقت run_dt
            job_id = f"hw-{hw_id}-{days_before}"
            try:
                self.scheduler.remove_job(job_id)
            except JobLookupError:
                pass
            except Exception:
                pass

            try:
                callable_ref = f"{__name__}:send_hw_reminder"
                self.scheduler.add_job(callable_ref, 'date', run_date=run_dt, args=[hw_id, days_before, self.db_path], id=job_id, replace_existing=True)
                logger.info("Scheduled job %s at %s", job_id, run_dt)
            except Exception:
                logger.exception("Failed to add scheduler job %s", job_id)

    def schedule_daily_backup(self, hour: int = 3, minute: int = 0):
        try:
            job_id = "backup_db_daily"
            callable_ref = f"{__name__}:backup_db_once"
            self.scheduler.add_job(callable_ref, 'cron', hour=hour, minute=minute, args=[self.db_path, self.backup_dir], id=job_id, replace_existing=True)
            logger.info("Scheduled daily backup (cron) at %02d:%02d", hour, minute)
            return True
        except Exception:
            logger.exception("Failed to schedule daily backup")
            return False

    def backup_db_once(self):
        try:
            backup_db_once(self.db_path, self.backup_dir)
        except Exception:
            logger.exception("backup_db_once wrapper failed")

    def bootstrap_all(self):
        try:
            conn = get_conn(self.db_path)
            cur = conn.cursor()
            
            placeholder = "%s" if DB_TYPE == "postgresql" else "?"
            
            # For PostgreSQL, set up row factory
            if DB_TYPE == "postgresql":
                import psycopg2.extras
                cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cur.execute("SELECT * FROM homeworks WHERE done = 0")
            else:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("SELECT * FROM homeworks WHERE done = 0")
            
            rows = cur.fetchall()
            for r in rows:
                try:
                    self.schedule_homework_reminders(r)
                except Exception:
                    logger.exception("schedule error for row id %s", r['id'] if 'id' in r.keys() else "<unknown>")
            
            
            try:
                cur.execute("SELECT * FROM custom_reminders")
                custom_reminders = cur.fetchall()
                from datetime import datetime
                now = datetime.now()
                for cr in custom_reminders:
                    try:
                        reminder_dt = datetime.strptime(cr['reminder_datetime'], "%Y-%m-%d %H:%M")
                        if reminder_dt > now:
                            reminder_id = cr['id']
                            user_id = cr['user_id']
                            job_id = f"custom_reminder-{reminder_id}"
                            callable_ref = "handlers:_job_send_custom_reminder"
                            self.scheduler.add_job(callable_ref, 'date', run_date=reminder_dt, args=[reminder_id, user_id], id=job_id, replace_existing=True)
                            logger.info("Bootstrap: scheduled custom reminder %s at %s", reminder_id, reminder_dt)
                    except Exception:
                        logger.exception("Failed to bootstrap custom reminder id %s", cr.get('id', '<unknown>'))
            except Exception:
                logger.exception("Failed to bootstrap custom reminders")
            
            close_conn(conn)
            # Only backup SQLite databases
            if DB_TYPE == "sqlite":
                backup_db_once(self.db_path, self.backup_dir)
                self.schedule_daily_backup(hour=3, minute=0)
            logger.info("Bootstrap completed — scheduled existing reminders and backups.")
        except Exception:
            logger.exception("Failed during bootstrap_all")
