@echo off
title AI Trader (Auto-Restart)
cd /d "c:\Users\ronbr\ai_trader"

:loop
echo.
echo ==========================================
echo  AI Trader starting at %date% %time%
echo  Access at: http://localhost:8501
echo ==========================================
streamlit run app.py --server.port 8501 --server.headless true --server.address 0.0.0.0
echo.
echo AI Trader stopped. Restarting in 15 seconds...
timeout /t 15 /nobreak > NUL
goto loop
