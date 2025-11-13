




```bash
pip install python-dotenv
```

أو:
```bash
pip install -r requirements.txt
```



1. أنشئ ملف `.env` في المجلد الرئيسي للمشروع
2. أضف المتغيرات التالية:

```env
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789,987654321
DB_PATH=reminders.db
BACKUP_DIR=backups
LOG_FILE=bot.log
```

3. لتشغيل البوت، استخدم:
```bash
python bot.py
```

**ملاحظة:** الكود يحاول تحميل `python-dotenv` تلقائياً. إذا كان مثبتاً، سيتم تحميل ملف `.env` تلقائياً. إذا لم يكن مثبتاً، يمكنك استخدام الطريقة الثانية.




```powershell
$env:BOT_TOKEN="your_bot_token_here"
$env:ADMIN_IDS="123456789,987654321"
python bot.py
```


```cmd
set BOT_TOKEN=your_bot_token_here
set ADMIN_IDS=123456789,987654321
python bot.py
```


```bash
export BOT_TOKEN="your_bot_token_here"
export ADMIN_IDS="123456789,987654321"
python bot.py
```



- **BOT_TOKEN** (مطلوب): معرف البوت من BotFather
- **ADMIN_IDS** (موصى به بشدة): معرفات الأدمن مفصولة بفواصل (مثال: `123456789,987654321`)
  - ⚠️ **تحذير أمني**: بدون ADMIN_IDS، البوت يعمل بدون حماية!




- **DB_PATH**: مسار قاعدة البيانات (افتراضي: `reminders.db`)
- **BACKUP_DIR**: مجلد النسخ الاحتياطي (افتراضي: `backups`)


- **LOG_FILE**: ملف السجل (افتراضي: `bot.log`)
- **LOG_LEVEL**: مستوى السجلات - DEBUG, INFO, WARNING, ERROR, CRITICAL (افتراضي: `INFO`)
- **LOG_MAX_SIZE**: الحد الأقصى لحجم ملف السجل بالبايت (افتراضي: `10485760` = 10MB)


- **API_TIMEOUT**: مهلة انتظار API بالثواني (افتراضي: `30`)
- **MAX_RETRIES**: عدد المحاولات عند فشل الطلب (افتراضي: `3`)


- **DEFAULT_REMINDERS**: التذكيرات الافتراضية بالأيام قبل الموعد (افتراضي: `3,2,1`)


- **BACKUP_ENABLED**: تفعيل النسخ الاحتياطي التلقائي - true/false (افتراضي: `true`)
- **BACKUP_INTERVAL_HOURS**: فترة النسخ الاحتياطي بالساعات (افتراضي: `24`)
- **MAX_BACKUP_FILES**: عدد ملفات النسخ الاحتياطي المحفوظة (افتراضي: `7`)


- **DEBUG_MODE**: وضع التطوير - true/false (افتراضي: `false`)



```env
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789,987654321
DB_PATH=reminders.db
BACKUP_DIR=backups
LOG_FILE=bot.log
LOG_LEVEL=INFO
API_TIMEOUT=30
MAX_RETRIES=3
DEFAULT_REMINDERS=3,2,1
BACKUP_ENABLED=true
BACKUP_INTERVAL_HOURS=24
MAX_BACKUP_FILES=7
DEBUG_MODE=false
```

