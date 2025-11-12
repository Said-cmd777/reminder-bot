# 📋 قائمة الملفات في مجلد "Reminder bot"

## 📁 الملفات الرئيسية (Core Files)

### ملفات Python الأساسية
- `bot.py` - الملف الرئيسي لتشغيل البوت
- `handlers.py` - معالجات الرسائل والـ callbacks
- `config.py` - إعدادات البوت (BOT_TOKEN, ADMIN_IDS, etc.)
- `constants.py` - الثوابت (callback data)
- `scheduler.py` - جدولة التذكيرات والنسخ الاحتياطي
- `run_bot_service.py` - Service manager للتشغيل 24/7

### ملفات قاعدة البيانات
- `db.py` - قاعدة البيانات الرئيسية (users, homeworks, reminders)
- `db_schedule.py` - قاعدة بيانات الجداول الأسبوعية
- `db_utils.py` - أدوات قاعدة البيانات (db_connection, safe_get)

### ملفات المساعدة
- `utils.py` - أدوات مساعدة (logging, parsing)
- `validators.py` - التحقق من صحة المدخلات

### ملفات الجداول الأسبوعية
- `weekly_schedule.py` - منطق الجداول الأسبوعية والحصص الدورية
- `init_schedule_db.py` - تهيئة قاعدة بيانات الجداول
- `init_group2_schedule.py` - تهيئة جدول Group 2
- `init_group3_schedule.py` - تهيئة جدول Group 3
- `init_group4_schedule.py` - تهيئة جدول Group 4

---

## 📁 مجلد bot_handlers

- `bot_handlers/__init__.py`
- `bot_handlers/base.py` - BotHandlers class, StateManager
- `bot_handlers/helpers.py` - دوال مساعدة (keyboards, formatting)
- `bot_handlers/schedule_admin_helpers.py` - مساعدات إدارة الجداول
- `bot_handlers/weekly_schedule_helpers.py` - مساعدات الجداول الأسبوعية

---

## 📁 ملفات النشر (Deployment Files)

- `Procfile` - ملف تعريف لـ Render.com
- `requirements.txt` - المكتبات المطلوبة
- `.gitignore` - ملفات يتم تجاهلها عند الرفع إلى GitHub
- `upload_to_github.bat` - Script لرفع الملفات إلى GitHub

---

## 📁 ملفات التشغيل (Startup Files)

- `start_bot.bat` - تشغيل البوت (Windows)
- `start_bot_forever.bat` - تشغيل البوت في الخلفية 24/7
- `start_bot_service.ps1` - PowerShell script للتشغيل

---

## 📁 ملفات التوثيق (Documentation)

### أدلة النشر
- `README_FIRST.md` - ابدأ من هنا - دليل شامل
- `README_DEPLOY.md` - دليل نشر البوت (شامل)
- `RENDER_DEPLOY_GUIDE.md` - دليل نشر البوت على Render.com
- `DEPLOY_RENDER.md` - دليل نشر Render.com
- `HOW_TO_DEPLOY.md` - كيفية النشر
- `QUICK_DEPLOY.md` - نشر سريع
- `START_HERE.md` - ابدأ من هنا

### أدلة GitHub
- `README_GITHUB.md` - دليل رفع الملفات إلى GitHub
- `GITHUB_UPLOAD_GUIDE.md` - دليل رفع الملفات إلى GitHub (شامل)
- `GITHUB_STEPS.md` - خطوات رفع الملفات إلى GitHub
- `GITHUB_QUICK_START.md` - بدء سريع GitHub
- `ابدأ_من_هنا_رفع_الى_GitHub.md` - دليل رفع الملفات (عربي)
- `كيف_ترفع_الملفات_الى_GitHub.md` - دليل شامل رفع الملفات (عربي)
- `خطوات_رفع_الملفات_الى_GitHub.txt` - خطوات نصية بسيطة

### أدلة أخرى
- `README_24_7.md` - دليل التشغيل 24/7
- `QUICK_START_24_7.md` - بدء سريع 24/7
- `README_ENV.md` - دليل متغيرات البيئة
- `README_PDF_SETUP.md` - دليل إعداد PDF
- `SCHEDULE_ADMIN_GUIDE.md` - دليل إدارة الجداول
- `SCHEDULE_PDF_GUIDE.md` - دليل PDF الجداول
- `HANDLERS_REFACTORING.md` - توثيق إعادة هيكلة handlers

---

## 📁 ملفات أخرى

- `migrate_db.py` - ترحيل قاعدة البيانات
- `test_config.py` - اختبار الإعدادات
- `view_users.py` - عرض المستخدمين
- `view_users_fixed.py` - عرض المستخدمين (مصحح)
- `قائمة_الملفات.txt` - قائمة الملفات (نصي)

---

## 📁 المجلدات

- `backups/` - مجلد النسخ الاحتياطي
- `schedules/` - مجلد ملفات PDF للجداول
- `venv/` - Virtual Environment (Python)
- `bot_handlers/` - معالجات البوت
- `handlers/` - مجلد handlers (فارغ)
- `__pycache__/` - ملفات Python المترجمة

---

## 📁 ملفات قاعدة البيانات

- `reminders.db` - ملف قاعدة البيانات (SQLite)
- `reminders.db-shm` - ملف SQLite (shared memory)
- `reminders.db-wal` - ملف SQLite (write-ahead log)
- `reminders.db.bak` - نسخة احتياطية من قاعدة البيانات

---

## 📁 ملفات اللوغات

- `bot.log` - لوغات البوت
- `bot_service.log` - لوغات service manager (إن وجد)

---

## ✅ الملفات المطلوبة للنشر على Render.com

### ملفات Python الأساسية
1. `bot.py`
2. `handlers.py`
3. `config.py`
4. `constants.py`
5. `db.py`
6. `db_schedule.py`
7. `db_utils.py`
8. `scheduler.py`
9. `utils.py`
10. `validators.py`
11. `weekly_schedule.py`
12. `run_bot_service.py`

### مجلد bot_handlers
- `bot_handlers/__init__.py`
- `bot_handlers/base.py`
- `bot_handlers/helpers.py`
- `bot_handlers/schedule_admin_helpers.py`
- `bot_handlers/weekly_schedule_helpers.py`

### ملفات النشر
- `requirements.txt`
- `Procfile`
- `.gitignore`

---

## ❌ ملفات لا يجب رفعها إلى GitHub

- `.env` - متغيرات البيئة (يحتوي على BOT_TOKEN)
- `*.db` - ملفات قاعدة البيانات (سيتم إنشاؤها)
- `*.log` - ملفات اللوغات
- `venv/` - Virtual Environment
- `__pycache__/` - ملفات Python المترجمة
- `backups/` - النسخ الاحتياطي
- `schedules/` - ملفات PDF (اختياري)

---

## 📊 إحصائيات

- **إجمالي ملفات Python:** ~20 ملف
- **إجمالي ملفات التوثيق:** ~20 ملف
- **إجمالي ملفات النشر:** 4 ملفات
- **إجمالي المجلدات:** 6 مجلدات

---

## 🎯 الملفات الأكثر أهمية

1. `bot.py` - الملف الرئيسي
2. `handlers.py` - معالجات الرسائل
3. `config.py` - الإعدادات
4. `db.py` - قاعدة البيانات
5. `run_bot_service.py` - Service manager
6. `requirements.txt` - المكتبات المطلوبة
7. `Procfile` - ملف تعريف Render.com

---

## 📚 للمزيد من المعلومات

- راجع `README_FIRST.md` للدليل الشامل
- راجع `قائمة_الملفات.txt` للقائمة النصية

