# 🔧 دليل إصلاح مشاكل Replit

## ✅ التغييرات المطبقة

### 1. **Timezone Support** 🌍
- ✅ أضيف `pytz` إلى `requirements.txt`
- ✅ `SchedulerManager` يدعم الآن timezone
- ✅ افتراضي: `Africa/Algiers` (الجزائر)
- ✅ يمكن تغييره عبر متغير البيئة `TIMEZONE`

### 2. **Keep-Alive (Flask)** 🔄
- ✅ أضيف `Flask` إلى `requirements.txt`
- ✅ Flask server يعمل على port 8080 (لـ Replit)
- ✅ Routes: `/` و `/health`
- ✅ يعمل تلقائياً على Replit فقط

### 3. **Database على Replit** 💾
- ✅ على Replit: يحفظ DB في `~/.local/share/reminders.db`
- ✅ محلياً: يستخدم `reminders.db` (كما هو)

### 4. **تحسينات Logging** 📝
- ✅ logging تفصيلي لجدولة التذكيرات
- ✅ معلومات timezone في startup banner

---

## 🚀 خطوات النشر على Replit

### 1. **رفع الكود إلى GitHub**
```bash
git add .
git commit -m "Fix: Add timezone support and keep-alive for Replit"
git push
```

### 2. **على Replit**
1. افتح Repl الخاص بك
2. Replit سيتحدث الكود تلقائياً من GitHub
3. تأكد من تثبيت المتطلبات:
   ```bash
   pip install -r requirements.txt
   ```

### 3. **متغيرات البيئة**
في Replit → Secrets (🔒):
- `BOT_TOKEN`: رمز البوت
- `ADMIN_IDS`: معرفات الأدمن (مفصولة بفواصل)
- `TIMEZONE`: (اختياري) timezone (افتراضي: `Africa/Algiers`)

### 4. **UptimeRobot (مهم!)** 🔄
1. سجل في https://uptimerobot.com (مجاني)
2. أضف Monitor:
   - URL: `https://your-repl-name.your-username.repl.co`
   - Interval: كل 5 دقائق
   - Type: HTTP(s)

**النتيجة:** Replit لن ينام أبداً! ✅

---

## 🧪 التحقق من النجاح

### في Replit Console، يجب أن ترى:
```
🚀 Bot is running on Replit!
🌍 Timezone: Africa/Algiers
⏰ Current time: 2025-11-14 23:43:40+01:00
🌐 Keep-Alive: Running on port 8080
📡 Status: Polling...
```

### عند إضافة واجب بـ `reminders = 0`:
```
INFO: schedule_homework_reminders: hw_id=X, remind_spec='0'
INFO: schedule_homework_reminders: sending immediate reminder (days_before=0)
INFO: schedule_homework_reminders: successfully sent immediate reminder
```

---

## ⚙️ إعدادات إضافية

### تغيير Timezone:
في `.env` أو Replit Secrets:
```
TIMEZONE=Africa/Cairo
```

### قائمة Timezones الشائعة:
- `Africa/Algiers` (الجزائر) - UTC+1
- `Africa/Cairo` (مصر) - UTC+2
- `Asia/Riyadh` (السعودية) - UTC+3
- `Asia/Dubai` (الإمارات) - UTC+4

---

## ❓ حل المشاكل

### المشكلة: Keep-Alive لا يعمل
**الحل:** تأكد من أن Flask مثبت:
```bash
pip install Flask
```

### المشكلة: Timezone لا يعمل
**الحل:** تأكد من أن pytz مثبت:
```bash
pip install pytz
```

### المشكلة: Database تُحذف
**الحل:** على Replit، DB تُحفظ في `~/.local/share/reminders.db` - هذا مجلد مستقر.

### المشكلة: التذكيرات لا تُرسل
**الحل:**
1. تحقق من السجلات
2. تأكد من أن `reminders = '0'` (ليس `None`)
3. تحقق من أن الموعد في الماضي أو الآن

---

## 📚 مراجع

- APScheduler Timezone: https://apscheduler.readthedocs.io/en/stable/userguide.html#timezone
- Flask: https://flask.palletsprojects.com/
- UptimeRobot: https://uptimerobot.com
- Replit Always On: https://replit.com/pricing

