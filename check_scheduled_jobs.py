"""
سكريبت للتحقق من الوظائف المجدولة في APScheduler.
"""
import sqlite3
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from scheduler import SchedulerManager
from config import DB_PATH

def check_scheduled_jobs():
    """التحقق من الوظائف المجدولة."""
    print("=" * 60)
    print("فحص الوظائف المجدولة في APScheduler")
    print("=" * 60)
    
    # إنشاء scheduler مؤقت للفحص
    scheduler = BackgroundScheduler(jobstores={'default': MemoryJobStore()})
    scheduler.start()
    
    try:
        # فحص الواجبات من قاعدة البيانات
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM homeworks WHERE done = 0")
        homeworks = cur.fetchall()
        
        print(f"\nعدد الواجبات غير المكتملة: {len(homeworks)}")
        
        for hw in homeworks:
            hw_id = hw['id']
            subject = hw['subject']
            due_at = hw['due_at']
            reminders = hw.get('reminders', 'default')
            
            print(f"\nالواجب ID: {hw_id} - {subject}")
            print(f"  الموعد: {due_at}")
            print(f"  التذكيرات: {reminders}")
            
            # حساب التذكيرات المطلوبة
            try:
                due_dt = datetime.strptime(due_at, "%Y-%m-%d %H:%M")
                now = datetime.now()
                
                if reminders and reminders.lower() != 'default':
                    reminder_days = [int(x.strip()) for x in reminders.split(',')]
                else:
                    reminder_days = [3, 2, 1]  # default
                
                print(f"  التذكيرات المطلوبة: {reminder_days} أيام قبل الموعد")
                
                scheduled_count = 0
                for days_before in reminder_days:
                    run_dt = due_dt - timedelta(days=days_before)
                    if run_dt > now:
                        job_id = f"hw-{hw_id}-{days_before}"
                        print(f"    ✓ يجب جدولة: {job_id} في {run_dt}")
                        scheduled_count += 1
                    else:
                        print(f"    ✗ مرّ الموعد: {days_before} أيام قبل (كان يجب أن يكون في {run_dt})")
                
                if scheduled_count == 0:
                    print(f"  ⚠️  لا توجد تذكيرات مجدولة (جميعها مرت)")
                else:
                    print(f"  ✓ يجب أن يكون هناك {scheduled_count} تذكير مجدول")
                    
            except Exception as e:
                print(f"  ⚠️  خطأ في حساب التذكيرات: {e}")
        
        conn.close()
        
    finally:
        scheduler.shutdown()
    
    print("\n" + "=" * 60)
    print("ملاحظة: هذا الفحص لا يتحقق من الوظائف الفعلية في scheduler البوت")
    print("للتحقق الفعلي، راجع ملف bot.log أو شغّل البوت وافحص scheduler.get_jobs()")
    print("=" * 60)

if __name__ == "__main__":
    from datetime import timedelta
    check_scheduled_jobs()

