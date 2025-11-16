"""فحص reminders في قاعدة البيانات"""
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('reminders.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute('SELECT id, subject, due_at, reminders, done FROM homeworks WHERE done = 0')
rows = cur.fetchall()

print('=' * 60)
print('فحص الواجبات غير المكتملة:')
print('=' * 60)

for r in rows:
    print(f'\nID: {r[0]}')
    print(f'  Subject: {r[1]}')
    print(f'  Due: {r[2]}')
    print(f'  Reminders: "{r[3]}" (type: {type(r[3]).__name__})')
    print(f'  Done: {r[4]}')
    
    # تحليل reminders
    remind_spec = r[3]
    if not remind_spec:
        remind_spec = "3,2,1"
        print(f'  -> Using default: {remind_spec}')
    else:
        print(f'  -> Using: {remind_spec}')
    
    # تحويل إلى offsets
    offsets = []
    for part in str(remind_spec).split(","):
        p = part.strip()
        if not p:
            continue
        try:
            v = int(p)
            if 0 <= v <= 3650:
                offsets.append(v)
                print(f'  -> Offset: {v}')
        except Exception as e:
            print(f'  -> Error parsing "{p}": {e}')
    
    if not offsets:
        offsets = [3, 2, 1]
        print(f'  -> No valid offsets, using default: {offsets}')
    else:
        print(f'  -> Final offsets: {offsets}')
    
    # حساب run_dt لكل offset
    try:
        due = datetime.strptime(r[2], "%Y-%m-%d %H:%M")
        now = datetime.now()
        print(f'  -> Due: {due}')
        print(f'  -> Now: {now}')
        
        for days_before in offsets:
            run_dt = due - timedelta(days=days_before)
            time_diff = (run_dt - now).total_seconds()
            print(f'  -> days_before={days_before}: run_dt={run_dt}, diff={time_diff:.0f} seconds')
            
            if days_before == 0:
                if time_diff <= 0:
                    print(f'      -> Should schedule immediately (days_before=0, past/now)')
                else:
                    print(f'      -> Should schedule at due time (days_before=0, future)')
            else:
                if time_diff < 0:
                    print(f'      -> Should skip (past)')
                else:
                    print(f'      -> Should schedule (future)')
    except Exception as e:
        print(f'  -> Error parsing due date: {e}')

conn.close()

print('\n' + '=' * 60)

