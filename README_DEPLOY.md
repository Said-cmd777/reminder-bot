# دليل نشر البوت على استضافة مجانية (24/7)

هذا الدليل يشرح كيفية نشر البوت على استضافة مجانية بحيث يعمل 24/7 بدون الحاجة للكمبيوتر.

## الخيارات المجانية المتاحة

### 1. Render.com (مُوصى به) ⭐

**الميزات:**
- ✅ مجاني تماماً
- ✅ يعمل 24/7 بدون انقطاع
- ✅ سهل الاستخدام
- ✅ يدعم Python
- ✅ قاعدة بيانات مجانية (PostgreSQL)
- ✅ SSL تلقائي
- ✅ تحديثات تلقائية من GitHub

**القيود:**
- قد ينام بعد 15 دقيقة من عدم الاستخدام (لكن يمكن تفعيله بسرعة)
- 512 MB RAM
- 0.1 CPU

**السعر:** مجاني تماماً

---

### 2. Railway.app

**الميزات:**
- ✅ مجاني (مع حدود)
- ✅ سهل الاستخدام
- ✅ يدعم Python
- ✅ قاعدة بيانات مجانية

**القيود:**
- $5 مجاناً شهرياً (حوالي 500 ساعة)
- بعد استنفاد الساعات، يحتاج دفع

**السعر:** مجاني محدود

---

### 3. Fly.io

**الميزات:**
- ✅ مجاني
- ✅ موثوق
- ✅ يدعم Python

**القيود:**
- 3 VMs مجانية
- 256 MB RAM لكل VM

**السعر:** مجاني

---

### 4. Oracle Cloud Always Free

**الميزات:**
- ✅ مجاني تماماً (دون انتهاء)
- ✅ موارد كبيرة (2 AMD VMs)
- ✅ يعمل 24/7
- ✅ موثوق جداً

**القيود:**
- يحتاج تسجيل حساب Oracle
- إعداد أكثر تعقيداً

**السعر:** مجاني تماماً

---

## الطريقة المُوصى بها: Render.com

### الخطوة 1: إعداد GitHub Repository

1. **إنشاء حساب على GitHub** (إذا لم يكن لديك)
   - اذهب إلى https://github.com
   - أنشئ حساب جديد

2. **رفع الكود إلى GitHub**
   ```bash
   # في مجلد المشروع
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git push -u origin main
   ```

### الخطوة 2: إعداد Render.com

1. **إنشاء حساب على Render**
   - اذهب إلى https://render.com
   - سجّل بحساب GitHub

2. **إنشاء Web Service جديد**
   - اضغط على "New +" → "Web Service"
   - اختر Repository الخاص بك
   - اضبط الإعدادات:
     - **Name:** telegram-bot
     - **Environment:** Python 3
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `python run_bot_service.py`
     - **Plan:** Free

3. **إضافة Environment Variables**
   - اضغط على "Environment"
   - أضف المتغيرات:
     ```
     BOT_TOKEN=your_bot_token_here
     ADMIN_IDS=123456789,987654321
     DB_PATH=/opt/render/project/src/reminders.db
     BACKUP_DIR=/opt/render/project/src/backups
     LOG_FILE=/opt/render/project/src/bot.log
     SCHEDULES_DIR=/opt/render/project/src/schedules
     ```

4. **تفعيل Auto-Deploy**
   - اضغط على "Settings"
   - فعّل "Auto-Deploy"

### الخطوة 3: التأكد من العمل

1. **مراقبة اللوغات**
   - اضغط على "Logs" في Render Dashboard
   - تحقق من أن البوت يعمل بدون أخطاء

2. **اختبار البوت**
   - أرسل `/start` للبوت
   - تحقق من أن البوت يرد

---

## طريقة بديلة: Railway.app

### الخطوة 1: إعداد Railway

1. **إنشاء حساب على Railway**
   - اذهب إلى https://railway.app
   - سجّل بحساب GitHub

2. **إنشاء مشروع جديد**
   - اضغط على "New Project"
   - اختر "Deploy from GitHub repo"
   - اختر Repository الخاص بك

3. **إضافة Environment Variables**
   - اضغط على "Variables"
   - أضف:
     ```
     BOT_TOKEN=your_bot_token_here
     ADMIN_IDS=123456789,987654321
     ```

4. **تغيير Start Command**
   - اضغط على "Settings"
   - غيّر "Start Command" إلى: `python run_bot_service.py`

---

## طريقة متقدمة: Oracle Cloud Always Free

### الخطوة 1: إنشاء حساب Oracle Cloud

1. **التسجيل**
   - اذهب إلى https://www.oracle.com/cloud/free/
   - سجّل حساب جديد (يحتاج بطاقة ائتمان للتحقق)

2. **إنشاء VM Instance**
   - اذهب إلى "Compute" → "Instances"
   - اضغط على "Create Instance"
   - اختر:
     - **Shape:** VM.Standard.A1.Flex (Always Free)
     - **OS:** Ubuntu 22.04
     - **SSH Key:** أنشئ مفتاح SSH

### الخطوة 2: إعداد البوت على VM

1. **الاتصال بالVM**
   ```bash
   ssh -i your_key.pem ubuntu@your_vm_ip
   ```

2. **تثبيت Python والمتطلبات**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip git -y
   ```

3. **رفع الكود**
   ```bash
   git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   cd YOUR_REPO_NAME
   pip3 install -r requirements.txt
   ```

4. **إعداد Environment Variables**
   ```bash
   nano .env
   # أضف:
   BOT_TOKEN=your_bot_token_here
   ADMIN_IDS=123456789,987654321
   ```

5. **تشغيل البوت كخدمة**
   ```bash
   sudo nano /etc/systemd/system/telegram-bot.service
   ```
   
   أضف:
   ```ini
   [Unit]
   Description=Telegram Bot Service
   After=network.target

   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/YOUR_REPO_NAME
   Environment="PATH=/usr/bin:/usr/local/bin"
   ExecStart=/usr/bin/python3 /home/ubuntu/YOUR_REPO_NAME/run_bot_service.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

6. **تفعيل الخدمة**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable telegram-bot
   sudo systemctl start telegram-bot
   sudo systemctl status telegram-bot
   ```

---

## مقارنة الخيارات

| الخيار | السعر | الموثوقية | سهولة الاستخدام | الموارد |
|--------|-------|-----------|-----------------|---------|
| **Render.com** | مجاني | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | محدودة |
| **Railway.app** | مجاني محدود | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | محدودة |
| **Fly.io** | مجاني | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | محدودة |
| **Oracle Cloud** | مجاني | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## نصائح مهمة

### 1. استخدام قاعدة بيانات خارجية (مُوصى به)

بدلاً من SQLite المحلي، استخدم قاعدة بيانات مجانية:

#### Option A: PostgreSQL على Render
- Render يوفر PostgreSQL مجاني
- غير `DB_PATH` لاستخدام PostgreSQL

#### Option B: SQLite مع Backup تلقائي
- استخدم SQLite المحلي
- قم بنسخ احتياطي يومي إلى GitHub

### 2. مراقبة اللوغات

- راقب اللوغات بانتظام في Dashboard
- تحقق من الأخطاء بشكل دوري

### 3. تحديثات تلقائية

- فعّل Auto-Deploy من GitHub
- كل push جديد سيُحدث البوت تلقائياً

### 4. إدارة قاعدة البيانات

- استخدم نسخ احتياطي تلقائي
- راقب حجم قاعدة البيانات

---

## استكشاف الأخطاء

### المشكلة: البوت لا يعمل

**الحل:**
1. تحقق من اللوغات في Dashboard
2. تحقق من Environment Variables
3. تحقق من أن `BOT_TOKEN` صحيح

### المشكلة: البوت يتوقف

**الحل:**
1. تحقق من أن `run_bot_service.py` يعمل
2. تحقق من إعدادات إعادة التشغيل
3. راقب استخدام الموارد

### المشكلة: قاعدة البيانات مفقودة

**الحل:**
1. استخدم قاعدة بيانات خارجية (PostgreSQL)
2. أو استخدم نسخ احتياطي تلقائي

---

## الخلاصة

**أسهل طريقة:** Render.com
- سهل الإعداد
- مجاني
- يعمل 24/7
- تحديثات تلقائية

**أفضل موارد:** Oracle Cloud
- مجاني تماماً
- موارد كبيرة
- موثوق جداً

**للمبتدئين:** Railway.app
- سهل جداً
- واجهة بسيطة
- مجاني محدود

---

## الخطوات التالية

1. اختر الاستضافة المناسبة
2. ارفع الكود إلى GitHub
3. اربط GitHub بالاستضافة
4. أضف Environment Variables
5. شغّل البوت
6. راقب اللوغات

---

## للمساعدة

إذا واجهت مشاكل:
1. تحقق من اللوغات
2. تحقق من Environment Variables
3. راجع التوثيق الرسمي للاستضافة
4. تحقق من أن جميع الملفات موجودة

