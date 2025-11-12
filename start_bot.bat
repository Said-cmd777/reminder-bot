@echo off
REM start_bot.bat - تشغيل البوت على Windows
REM هذا الملف يشغّل البوت في نافذة منفصلة

echo ========================================
echo Telegram Bot Service
echo ========================================
echo.

REM التحقق من وجود Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python first.
    pause
    exit /b 1
)

REM التحقق من وجود virtual environment
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo [WARNING] Virtual environment not found. Using system Python.
)

REM التحقق من وجود ملف bot.py
if not exist "bot.py" (
    echo [ERROR] bot.py not found in current directory.
    pause
    exit /b 1
)

REM التحقق من وجود ملف .env
if not exist ".env" (
    echo [WARNING] .env file not found. Make sure BOT_TOKEN is set.
)

echo.
echo Starting bot...
echo Press Ctrl+C to stop
echo ========================================
echo.

REM تشغيل البوت
python run_bot_service.py

pause

