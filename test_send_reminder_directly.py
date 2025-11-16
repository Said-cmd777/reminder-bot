"""
اختبار إرسال التذكير مباشرة بدون scheduler
"""
import sqlite3
import logging
from datetime import datetime
from scheduler import send_hw_reminder, scheduler_bot

# إعداد logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# فحص الواجب ID 22
conn = sqlite3.connect('reminders.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute('SELECT * FROM homeworks WHERE id = 22')
row = cur.fetchone()

if row:
    print(f"الواجب ID: {row['id']}")
    print(f"المادة: {row['subject']}")
    print(f"الموعد: {row['due_at']}")
    print(f"التذكيرات: {row['reminders']}")
    
    # محاولة إرسال التذكير مباشرة
    print("\nمحاولة إرسال التذكير مباشرة...")
    print(f"scheduler_bot: {scheduler_bot}")
    
    if scheduler_bot is None:
        print("⚠️ scheduler_bot غير مضبوط - هذا هو السبب!")
        print("التذكيرات لا تُرسل لأن scheduler_bot = None")
    else:
        print("✅ scheduler_bot مضبوط")
        # محاولة إرسال التذكير
        try:
            send_hw_reminder(22, 0, 'reminders.db')
            print("✅ تم استدعاء send_hw_reminder")
        except Exception as e:
            print(f"❌ خطأ في send_hw_reminder: {e}")
            import traceback
            traceback.print_exc()
else:
    print("لم أجد الواجب ID 22")

conn.close()

