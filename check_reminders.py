"""
سكريبت للتحقق من حالة التذكيرات وإعدادات الإشعارات.
"""
import sqlite3
from datetime import datetime
from db_utils import db_connection, safe_get
from db import get_notification_setting, get_all_homeworks

def check_reminders_status():
    """التحقق من حالة التذكيرات وإعدادات الإشعارات."""
    print("=" * 60)
    print("فحص حالة التذكيرات وإعدادات الإشعارات")
    print("=" * 60)
    
    with db_connection() as conn:
        # 1. فحص الواجبات
        print("\n1. الواجبات:")
        print("-" * 60)
        homeworks = get_all_homeworks(conn)
        if not homeworks:
            print("   لا توجد واجبات في قاعدة البيانات.")
        else:
            print(f"   عدد الواجبات: {len(homeworks)}")
            for hw in homeworks:
                hw_id = safe_get(hw, 'id', 'N/A')
                subject = safe_get(hw, 'subject', 'N/A')
                due_at = safe_get(hw, 'due_at', 'N/A')
                done = safe_get(hw, 'done', 0)
                reminders = safe_get(hw, 'reminders', 'default')
                target_user = safe_get(hw, 'target_user_id', None)
                
                print(f"\n   الواجب ID: {hw_id}")
                print(f"   المادة: {subject}")
                print(f"   الموعد: {due_at}")
                print(f"   حالة 'تم': {'نعم' if done else 'لا'}")
                print(f"   التذكيرات: {reminders}")
                print(f"   المستهدف: {'الجميع' if target_user is None else f'User ID: {target_user}'}")
                
                # حساب موعد التذكيرات
                try:
                    due_dt = datetime.strptime(due_at, "%Y-%m-%d %H:%M")
                    now = datetime.now()
                    days_until = (due_dt - now).days
                    print(f"   الأيام المتبقية: {days_until} يوم")
                    
                    # فحص التذكيرات المطلوبة
                    if reminders and reminders.lower() != 'default':
                        try:
                            reminder_days = [int(x.strip()) for x in reminders.split(',')]
                            print(f"   التذكيرات المطلوبة: {reminder_days} أيام قبل الموعد")
                            upcoming = [d for d in reminder_days if 0 <= days_until <= d]
                            if upcoming:
                                print(f"   ⚠️  التذكيرات القادمة: {upcoming} أيام")
                            else:
                                print(f"   ✓ لا توجد تذكيرات قادمة (إما مرت أو لم تأت بعد)")
                        except:
                            pass
                except:
                    print(f"   ⚠️  خطأ في تحليل التاريخ: {due_at}")
        
        # 2. فحص إعدادات الإشعارات للمستخدمين
        print("\n\n2. إعدادات الإشعارات للمستخدمين:")
        print("-" * 60)
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM users")
        users = cur.fetchall()
        if not users:
            print("   لا يوجد مستخدمون مسجلون.")
        else:
            print(f"   عدد المستخدمين: {len(users)}")
            for user_row in users:
                user_id = user_row[0]
                try:
                    hw_enabled = get_notification_setting(conn, user_id, 'homework_reminders')
                    manual_enabled = get_notification_setting(conn, user_id, 'manual_reminders')
                    custom_enabled = get_notification_setting(conn, user_id, 'custom_reminders')
                    
                    status = []
                    if not hw_enabled:
                        status.append("❌ تذكيرات الواجبات معطلة")
                    if not manual_enabled:
                        status.append("❌ تذكيرات الأدمين معطلة")
                    if not custom_enabled:
                        status.append("❌ التذكيرات المخصصة معطلة")
                    
                    if status:
                        print(f"\n   User ID: {user_id}")
                        for s in status:
                            print(f"      {s}")
                    else:
                        print(f"   User ID: {user_id}: ✅ جميع الإشعارات مفعّلة")
                except Exception as e:
                    print(f"   User ID: {user_id}: ⚠️  خطأ في فحص الإعدادات: {e}")
        
        # 3. فحص الواجبات المكتملة
        print("\n\n3. الواجبات المكتملة:")
        print("-" * 60)
        cur.execute("""
            SELECT hw_id, user_id, completed_at 
            FROM homework_completions 
            ORDER BY completed_at DESC 
            LIMIT 10
        """)
        completions = cur.fetchall()
        if not completions:
            print("   لا توجد واجبات مكتملة.")
        else:
            print(f"   آخر {len(completions)} إكمال:")
            for comp in completions:
                print(f"   - User {comp[1]} أكمل الواجب {comp[0]} في {comp[2]}")
    
    print("\n" + "=" * 60)
    print("انتهى الفحص")
    print("=" * 60)

if __name__ == "__main__":
    check_reminders_status()

