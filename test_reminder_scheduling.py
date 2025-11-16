"""
سكريبت لاختبار جدولة التذكيرات مع days_before=0
"""
import sqlite3
from datetime import datetime, timedelta
from scheduler import SchedulerManager
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.background import BackgroundScheduler
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# إنشاء bot وهمي للاختبار
class MockBot:
    def send_message(self, chat_id, text):
        print(f"[BOT] إرسال رسالة إلى {chat_id}: {text[:50]}...")
        return True
    
    def send_document(self, chat_id, file_id):
        print(f"[BOT] إرسال ملف إلى {chat_id}: {file_id}")
        return True

def test_reminder_scheduling():
    """اختبار جدولة التذكيرات"""
    print("=" * 60)
    print("اختبار جدولة التذكيرات")
    print("=" * 60)
    
    # إنشاء scheduler مؤقت
    bot = MockBot()
    scheduler = BackgroundScheduler(jobstores={'default': MemoryJobStore()})
    scheduler.start()
    
    try:
        # إنشاء SchedulerManager
        sch_mgr = SchedulerManager(
            bot=bot,
            db_path="reminders.db",
            backup_dir="backups",
            use_persistent_jobstore=False
        )
        
        # اختبار 1: واجب بموعد في الماضي و reminders=0
        print("\n[اختبار 1] واجب بموعد في الماضي و reminders=0")
        print("-" * 60)
        now = datetime.now()
        past_due = now - timedelta(hours=1)  # موعد قبل ساعة
        
        hw_row_past = {
            'id': 999,
            'subject': 'Test Past',
            'description': 'Test',
            'due_at': past_due.strftime("%Y-%m-%d %H:%M"),
            'pdf_type': None,
            'pdf_value': None,
            'conditions': '',
            'chat_id': 123456789,
            'done': 0,
            'reminders': '0',
            'target_user_id': None
        }
        
        print(f"الموعد: {past_due}")
        print(f"التذكيرات: 0")
        print(f"الآن: {now}")
        
        try:
            sch_mgr.schedule_homework_reminders(hw_row_past)
            print("✓ تم استدعاء schedule_homework_reminders")
        except Exception as e:
            print(f"✗ خطأ: {e}")
            import traceback
            traceback.print_exc()
        
        # فحص الوظائف المجدولة
        jobs = scheduler.get_jobs()
        print(f"\nعدد الوظائف المجدولة: {len(jobs)}")
        for job in jobs:
            print(f"  - Job ID: {job.id}, Run time: {job.next_run_time}")
        
        # اختبار 2: واجب بموعد في المستقبل و reminders=0
        print("\n[اختبار 2] واجب بموعد في المستقبل و reminders=0")
        print("-" * 60)
        future_due = now + timedelta(hours=1)  # موعد بعد ساعة
        
        hw_row_future = {
            'id': 998,
            'subject': 'Test Future',
            'description': 'Test',
            'due_at': future_due.strftime("%Y-%m-%d %H:%M"),
            'pdf_type': None,
            'pdf_value': None,
            'conditions': '',
            'chat_id': 123456789,
            'done': 0,
            'reminders': '0',
            'target_user_id': None
        }
        
        print(f"الموعد: {future_due}")
        print(f"التذكيرات: 0")
        print(f"الآن: {now}")
        
        try:
            sch_mgr.schedule_homework_reminders(hw_row_future)
            print("✓ تم استدعاء schedule_homework_reminders")
        except Exception as e:
            print(f"✗ خطأ: {e}")
            import traceback
            traceback.print_exc()
        
        # فحص الوظائف المجدولة
        jobs = scheduler.get_jobs()
        print(f"\nعدد الوظائف المجدولة: {len(jobs)}")
        for job in jobs:
            print(f"  - Job ID: {job.id}, Run time: {job.next_run_time}")
        
        # انتظار قليل لرؤية إذا تم تنفيذ الوظائف
        import time
        print("\nانتظار 3 ثواني لرؤية إذا تم تنفيذ الوظائف...")
        time.sleep(3)
        
    finally:
        scheduler.shutdown()

if __name__ == "__main__":
    test_reminder_scheduling()

