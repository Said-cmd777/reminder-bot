


Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Telegram Bot Service - PowerShell" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""


try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python version: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not found. Please install Python first." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}


if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & "venv\Scripts\Activate.ps1"
} else {
    Write-Host "[WARNING] Virtual environment not found. Using system Python." -ForegroundColor Yellow
}


if (-not (Test-Path "bot.py")) {
    Write-Host "[ERROR] bot.py not found in current directory." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}


if (-not (Test-Path ".env")) {
    Write-Host "[WARNING] .env file not found. Make sure BOT_TOKEN is set." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Starting bot service..." -ForegroundColor Green
Write-Host "The bot will restart automatically if it crashes." -ForegroundColor Green
Write-Host ""
Write-Host "To stop the bot, press Ctrl+C or close this window." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""


try {
    python run_bot_service.py
} catch {
    Write-Host "[ERROR] Failed to start bot: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Read-Host "Press Enter to exit"

