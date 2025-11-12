@echo off
REM start_bot_forever.bat - تشغيل البوت في الخلفية 24/7 على Windows
REM هذا الملف يشغّل البوت في نافذة منفصلة بدون إيقاف

echo ========================================
echo Telegram Bot Service - 24/7 Mode
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
echo Starting bot in background (24/7 mode)...
echo The bot will restart automatically if it crashes.
echo.
echo To stop the bot, close this window or use Task Manager.
echo ========================================
echo.

REM تشغيل البوت في نافذة منفصلة
start "Telegram Bot Service" /MIN cmd /c "python run_bot_service.py"

echo.
echo Bot started in background window.
echo Check bot_service.log for logs.
echo.
pause

