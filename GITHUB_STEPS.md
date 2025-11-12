# خطوات رفع الملفات إلى GitHub (مبسطة)

## الخطوة 1: تثبيت Git

1. اذهب إلى https://git-scm.com/download/win
2. حمّل Git for Windows
3. ثبّته (اضغط Next في جميع الخطوات)
4. أعد فتح Terminal

---

## الخطوة 2: إنشاء حساب GitHub

1. اذهب إلى https://github.com
2. اضغط "Sign up"
3. سجّل حساب جديد

---

## الخطوة 3: إنشاء Repository

1. اضغط "+" في الأعلى → "New repository"
2. أدخل اسم: `telegram-bot`
3. **⚠️ لا تضع علامة ✓ على "Add a README file"**
4. اضغط "Create repository"

---

## الخطوة 4: رفع الملفات

### افتح Terminal (PowerShell) واكتب:

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

---

## ⚠️ مهم: عند `git push`

سيطلب منك:
- **Username:** اسم المستخدم على GitHub
- **Password:** استخدم **Personal Access Token** (ليس كلمة المرور)

### كيفية الحصول على Personal Access Token:

1. اذهب إلى https://github.com/settings/tokens
2. اضغط "Generate new token (classic)"
3. اختر الصلاحيات: `repo` (جميعها)
4. اضغط "Generate token"
5. انسخ الرمز واستخدمه ككلمة مرور

---

## ✅ تم!

الآن ملفاتك على GitHub! 🎉

---

## الخطوة التالية

اذهب إلى Render.com لنشر البوت:
- راجع `RENDER_DEPLOY_GUIDE.md`

