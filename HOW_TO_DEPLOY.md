# كيفية نشر البوت على Render.com (مجاني 24/7)

## الخطوات (5 دقائق)

### 1. رفع الكود إلى GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### 2. إنشاء حساب Render.com

- اذهب إلى https://render.com
- سجّل بحساب GitHub

### 3. نشر البوت

1. **في Render Dashboard:**
   - اضغط "New +" → **"Background Worker"**
   - اختر Repository الخاص بك

2. **الإعدادات:**
   - **Name:** `telegram-bot`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python run_bot_service.py`
   - **Plan:** `Free`

3. **Environment Variables:**
   - اضغط "Advanced" → "Add Environment Variable"
   - أضف:
     ```
     BOT_TOKEN = your_bot_token_here
     ADMIN_IDS = 123456789,987654321
     ```

4. **النشر:**
   - اضغط "Create Background Worker"
   - انتظر حتى ينتهي Build

### 4. اختبار البوت

- أرسل `/start` للبوت في Telegram
- تحقق من أن البوت يرد ✅

---

## ✅ تم! البوت يعمل الآن 24/7 مجاناً!

---

## ⚠️ ملاحظة مهمة: قاعدة البيانات

Render.com يحذف الملفات عند إعادة النشر. استخدم:

**PostgreSQL على Render (مجاني):**
1. اضغط "New +" → "PostgreSQL"
2. اختر "Free" plan
3. أضف `DATABASE_URL` إلى Environment Variables

**أو:** استخدم SQLite مع نسخ احتياطي يومي

---

## للمزيد من التفاصيل

- راجع `RENDER_DEPLOY_GUIDE.md`
- راجع `README_DEPLOY.md`
- راجع `DEPLOY_RENDER.md`

