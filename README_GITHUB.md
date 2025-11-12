# 📤 كيفية رفع الملفات إلى GitHub

## 🎯 الطريقة الأسهل: استخدام GitHub Desktop

### الخطوة 1: تحميل GitHub Desktop

1. اذهب إلى: https://desktop.github.com
2. اضغط "Download for Windows"
3. ثبّت البرنامج
4. شغّل GitHub Desktop

### الخطوة 2: تسجيل الدخول

1. شغّل GitHub Desktop
2. اضغط "Sign in to GitHub.com"
3. سجّل دخول بحساب GitHub (أو أنشئ حساب جديد)

### الخطوة 3: إنشاء Repository على GitHub

1. اذهب إلى: https://github.com/new
2. أدخل:
   - **Repository name:** `telegram-bot` (أو أي اسم تريده)
   - **Description:** `Telegram Bot for Reminders` (اختياري)
   - **Public** أو **Private** (اختيارك)
3. **⚠️ مهم:** لا تضع علامة ✓ على "Add a README file"
4. اضغط "Create repository"

### الخطوة 4: رفع الملفات

1. في GitHub Desktop:
   - اضغط "File" → "Add local repository"
   - اختر مجلد `D:\Reminder bot`
   - اضغط "Add repository"

2. في الأسفل:
   - اكتب رسالة: `Initial commit`
   - اضغط "Commit to main"

3. اضغط "Publish repository"
   - اختر Repository الذي أنشأته
   - اضغط "Publish repository"

---

## ✅ تم! الملفات على GitHub الآن

---

## 🔧 الطريقة البديلة: استخدام Terminal

إذا كنت تريد استخدام Terminal:

### الخطوة 1: افتح Terminal (PowerShell)

1. اضغط `Win + R`
2. اكتب `powershell`
3. اضغط Enter

### الخطوة 2: اكتب الأوامر التالية

```bash
# 1. الانتقال إلى مجلد المشروع
cd "D:\Reminder bot"

# 2. تهيئة Git
git init

# 3. إضافة جميع الملفات
git add .

# 4. حفظ التغييرات
git commit -m "Initial commit"

# 5. تغيير اسم الفرع
git branch -M main

# 6. ربط المشروع بـ GitHub (استبدل YOUR_USERNAME و YOUR_REPO_NAME)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# 7. رفع الملفات
git push -u origin main
```

### ⚠️ عند `git push`:

سيطلب منك:
- **Username:** اسم المستخدم على GitHub
- **Password:** استخدم **Personal Access Token** (ليس كلمة المرور)

### كيفية الحصول على Personal Access Token:

1. اذهب إلى: https://github.com/settings/tokens
2. اضغط "Generate new token (classic)"
3. اختر الصلاحيات: `repo` (جميعها)
4. اضغط "Generate token"
5. انسخ الرمز واستخدمه ككلمة مرور

---

## 🚀 طريقة أسهل: استخدام ملف upload_to_github.bat

1. انقر نقراً مزدوجاً على `upload_to_github.bat`
2. اتبع التعليمات على الشاشة
3. أدخل رابط GitHub Repository عندما يُطلب منك

---

## ✅ التحقق من نجاح الرفع

1. اذهب إلى: https://github.com/YOUR_USERNAME/YOUR_REPO_NAME
2. تحقق من وجود جميع الملفات:
   - `bot.py`
   - `handlers.py`
   - `requirements.txt`
   - `Procfile`
   - وغيرها

---

## 🎯 الخطوة التالية

بعد رفع الملفات إلى GitHub:

1. **اذهب إلى Render.com:**
   - https://render.com
   - سجّل دخول بحساب GitHub

2. **انشر البوت:**
   - راجع `RENDER_DEPLOY_GUIDE.md`

---

## 💡 نصائح

1. ✅ **استخدم GitHub Desktop** إذا كنت مبتدئاً (أسهل طريقة)
2. ✅ **احفظ Personal Access Token** في مكان آمن
3. ✅ **لا ترفع ملف `.env`** (يحتوي على `BOT_TOKEN` - موجود في `.gitignore`)
4. ✅ **تحقق من `.gitignore`** قبل الرفع

---

## 🐛 حل المشاكل

### المشكلة: "fatal: not a git repository"
**الحل:** شغّل `git init` أولاً

### المشكلة: "fatal: remote origin already exists"
**الحل:** 
```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
```

### المشكلة: "error: failed to push some refs"
**الحل:**
```bash
git pull origin main --allow-unrelated-histories
git push -u origin main
```

---

## 📚 للمزيد من التفاصيل

- **دليل شامل:** راجع `GITHUB_UPLOAD_GUIDE.md`
- **خطوات مبسطة:** راجع `GITHUB_STEPS.md`
- **دليل سريع:** راجع `GITHUB_QUICK_START.md`

---

## 🎉 تم!

الآن ملفاتك على GitHub ويمكنك نشر البوت على Render.com!

