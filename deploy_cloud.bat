@echo off
title AI Trader - Cloud Deploy
cd /d "c:\Users\ronbr\ai_trader"
set GH=C:\Users\ronbr\AppData\Local\gh_cli\bin\gh.exe
set GIT=C:\Program Files\Git\cmd\git.exe

echo.
echo ==========================================
echo  AI Trader - GitHub Cloud Deploy
echo ==========================================
echo.

REM Check if already authenticated
"%GH%" auth status >nul 2>&1
if errorlevel 1 (
    echo [!] Not logged into GitHub.
    echo     Please run: gh auth login --web
    echo     Then re-run this script.
    pause
    exit /b 1
)

echo [OK] GitHub authenticated.

REM Create private repo and push (skip if remote already exists)
"%GIT%" remote get-url origin >nul 2>&1
if errorlevel 1 (
    echo [*] Creating GitHub repository...
    "%GH%" repo create ai-trader --private --source=. --push --remote origin
    if errorlevel 1 (
        echo [!] Repo creation failed. It may already exist. Trying to add remote...
        for /f "tokens=*" %%i in ('"%GH%" api user --jq .login') do set GHUSER=%%i
        "%GIT%" remote add origin https://github.com/%GHUSER%/ai-trader.git
        "%GIT%" push -u origin main
    )
) else (
    echo [*] Remote already exists. Pushing latest code...
    "%GIT%" push origin main
)

echo.
echo [*] Setting GitHub Secrets...
echo da059793952f45c3bfb2a2ff74ab02a4s | "%GH%" secret set TWELVE_DATA_API_KEY
echo ronbr30@gmail.com | "%GH%" secret set BOT_EMAIL

echo.
echo [*] Triggering first bot run now...
"%GH%" workflow run bot.yml

echo.
echo ==========================================
echo  DONE! Bot will now run in the cloud
echo  every 5 minutes during market hours
echo  (Mon-Fri 9am-5pm ET) — even if your
echo  PC is off.
echo ==========================================
echo.
echo  To see bot logs:
for /f "tokens=*" %%i in ('"%GH%" api user --jq .login') do echo  https://github.com/%%i/ai-trader/actions
echo.
pause
