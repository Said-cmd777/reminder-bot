# رفع الملفات إلى GitHub - دليل سريع 🚀

## الطريقة الأسهل: استخدام GitHub Desktop

### 1. تحميل GitHub Desktop
- اذهب إلى https://desktop.github.com
- حمّل GitHub Desktop وثبّته

### 2. تسجيل الدخول
- شغّل GitHub Desktop
- سجّل دخول بحساب GitHub

### 3. إضافة المشروع
- اضغط "File" → "Add local repository"
- اختر مجلد `D:\Reminder bot`
- اضغط "Add repository"

### 4. رفع الملفات
- اكتب رسالة: `Initial commit`
- اضغط "Commit to main"
- اضغط "Publish repository"
- اختر Repository (أو أنشئ واحد جديد)
- اضغط "Publish repository"

---

## ✅ تم! الملفات على GitHub الآن

---

## الطريقة البديلة: استخدام Terminal

### 1. افتح Terminal (PowerShell)
- اضغط `Win + R`
- اكتب `powershell`
- اضغط Enter

### 2. اكتب الأوامر التالية:

```bash
# الانتقال إلى مجلد المشروع
cd "D:\Reminder bot"

# تهيئة Git
git init

# إضافة جميع الملفات
git add .

# حفظ التغييرات
git commit -m "Initial commit"

# تغيير اسم الفرع
git branch -M main

# ربط المشروع بـ GitHub (استبدل YOUR_USERNAME و YOUR_REPO_NAME)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# رفع الملفات
git push -u origin main
```

---

## ⚠️ عند `git push`:

سيطلب منك:
- **Username:** اسم المستخدم على GitHub
- **Password:** استخدم **Personal Access Token** (ليس كلمة المرور)

### كيفية الحصول على Token:

1. اذهب إلى https://github.com/settings/tokens
2. اضغط "Generate new token (classic)"
3. اختر: `repo` (جميع الصلاحيات)
4. اضغط "Generate token"
5. انسخ الرمز واستخدمه ككلمة مرور

---

## 🎯 الخطوة التالية

بعد رفع الملفات إلى GitHub:
1. اذهب إلى Render.com
2. انشر البوت (راجع `RENDER_DEPLOY_GUIDE.md`)

---

## للمساعدة

- راجع `GITHUB_UPLOAD_GUIDE.md` للدليل الشامل
- راجع `GITHUB_STEPS.md` للخطوات المبسطة

