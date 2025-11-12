@echo off
REM upload_to_github.bat - Script لرفع الملفات إلى GitHub
REM هذا الملف يساعدك في رفع الملفات إلى GitHub بسهولة

echo ========================================
echo Upload to GitHub - Script
echo ========================================
echo.

REM التحقق من وجود Git
git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git not found. Please install Git first.
    echo Download from: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo [OK] Git is installed
echo.

REM الانتقال إلى مجلد المشروع
cd /d "%~dp0"
echo Current directory: %CD%
echo.

REM التحقق من وجود ملفات
if not exist "bot.py" (
    echo [ERROR] bot.py not found in current directory.
    pause
    exit /b 1
)

echo [OK] Project files found
echo.

REM تهيئة Git (إذا لم يكن موجوداً)
if not exist ".git" (
    echo Initializing Git repository...
    git init
    if errorlevel 1 (
        echo [ERROR] Failed to initialize Git repository
        pause
        exit /b 1
    )
    echo [OK] Git repository initialized
) else (
    echo [OK] Git repository already exists
)
echo.

REM إضافة جميع الملفات
echo Adding files to Git...
git add .
if errorlevel 1 (
    echo [ERROR] Failed to add files to Git
    pause
    exit /b 1
)
echo [OK] Files added to Git
echo.

REM حفظ التغييرات
echo Committing changes...
git commit -m "Initial commit - Telegram Bot"
if errorlevel 1 (
    echo [WARNING] Commit failed (may be because no changes)
)
echo [OK] Changes committed
echo.

REM تغيير اسم الفرع
echo Setting branch to main...
git branch -M main
if errorlevel 1 (
    echo [WARNING] Failed to set branch to main
)
echo [OK] Branch set to main
echo.

echo ========================================
echo Next Steps:
echo ========================================
echo.
echo 1. Create a new repository on GitHub:
echo    - Go to https://github.com/new
echo    - Enter repository name (e.g., telegram-bot)
echo    - DO NOT check "Add a README file"
echo    - Click "Create repository"
echo.
echo 2. Add the remote repository:
echo    git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
echo.
echo 3. Push the files:
echo    git push -u origin main
echo.
echo ========================================
echo.

REM السؤال إذا كان المستخدم يريد إضافة remote الآن
set /p add_remote="Do you want to add remote repository now? (y/n): "
if /i "%add_remote%"=="y" (
    set /p github_url="Enter GitHub repository URL (e.g., https://github.com/username/repo.git): "
    if not "%github_url%"=="" (
        echo.
        echo Adding remote repository...
        git remote remove origin 2>nul
        git remote add origin %github_url%
        if errorlevel 1 (
            echo [ERROR] Failed to add remote repository
            pause
            exit /b 1
        )
        echo [OK] Remote repository added
        echo.
        echo Pushing files to GitHub...
        echo Note: You will be asked for username and password
        echo Use Personal Access Token as password (not your GitHub password)
        echo.
        git push -u origin main
        if errorlevel 1 (
            echo [ERROR] Failed to push files to GitHub
            echo Please check your username and password/token
            pause
            exit /b 1
        )
        echo [OK] Files pushed to GitHub successfully!
        echo.
        echo ========================================
        echo Success! Your files are now on GitHub!
        echo ========================================
    )
) else (
    echo.
    echo You can add the remote repository manually later.
    echo Use the commands shown above.
)

echo.
pause

