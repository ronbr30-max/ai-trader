@echo off
title AI Trader V2
cd /d "c:\Users\ronbr\ai_trader"

echo.
echo ==========================================
echo  AI Trader V2 - 5-minute RSI Strategy
echo ==========================================
echo.

REM Kill any old processes
taskkill /f /im cloudflared.exe >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq AI Trader Bot V2" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq AI Trader Dashboard" >nul 2>&1

REM Start the V2 trading bot
echo Starting V2 trading bot...
start "AI Trader Bot V2" /min cmd /c "python bot_worker_v2.py ronbr30@gmail.com"

REM Start the dashboard
echo Starting dashboard...
start "AI Trader Dashboard" /min cmd /c "python -m streamlit run app.py --server.port 8501 --server.headless true --server.address 0.0.0.0"

REM Wait for everything to start
echo Waiting 8 seconds for services to come up...
timeout /t 8 /nobreak >nul

REM Start cloudflare tunnel
echo Starting public tunnel...
set LOGFILE=%TEMP%\cf_tunnel.log
start "CF Tunnel" /min cmd /c "cloudflared.exe tunnel --url http://localhost:8501 --no-autoupdate > %LOGFILE% 2>&1"

REM Wait for tunnel URL
echo Getting public URL (about 10 seconds)...
timeout /t 12 /nobreak >nul

REM Extract tunnel URL
for /f "tokens=*" %%i in ('powershell -NoProfile -Command "Select-String -Path \"%LOGFILE%\" -Pattern \"trycloudflare.com\" | Select-Object -First 1 | ForEach-Object { ($_ -split \"\s\") | Where-Object { $_ -like \"https://*.trycloudflare.com\" } | Select-Object -First 1 }" 2^>nul') do set CF_URL=%%i

echo.
echo ==========================================
echo  AI Trader V2 is RUNNING
echo.
echo  Strategy: 5-min RSI bounce
echo  Tickers: SPY, QQQ, BTC, ETH, AAPL, NVDA, TSLA
echo  TP: 1.5%%  ^|  SL: 0.5%%  ^|  Max 4 positions
echo.
echo  Dashboard:
echo    Local:  http://localhost:8501
if defined CF_URL (
    echo    Phone:  %CF_URL%
)
echo ==========================================
echo.
echo Keep this window open while trading.
echo Press any key to STOP everything.
echo.
pause >nul

REM Cleanup
echo Stopping all services...
taskkill /f /im cloudflared.exe >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq AI Trader Bot V2" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq AI Trader Dashboard" >nul 2>&1
echo Done.
timeout /t 2 /nobreak >nul
