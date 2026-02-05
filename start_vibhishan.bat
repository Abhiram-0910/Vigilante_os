@echo off
echo ===================================================
echo   VIBHISHAN (VIGILANTE-OS) - SYSTEM LAUNCHER
echo ===================================================
echo.
echo [1/2] Launching API Server (FastAPI + LangGraph)...
start "VIBHISHAN BRAIN" cmd /k "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

echo [2/2] Launching Command Center (Streamlit)...
start "VIBHISHAN DASHBOARD" cmd /k "streamlit run dashboard.py"

echo.
echo System components launched in separate windows.
echo Access Dashboard at: http://localhost:8501
echo Access API Docs at:  http://localhost:8000/docs
echo.
pause
