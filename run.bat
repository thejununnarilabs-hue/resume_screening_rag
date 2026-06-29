@echo off
REM Resume Screening System - Windows Launch Script

echo.
echo ========================================
echo Resume Screening & Ranking System
echo ========================================
echo.

REM Check if venv exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created.
)

REM Activate venv
call venv\Scripts\activate.bat

REM Check if dependencies installed
pip show streamlit > nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    echo Dependencies installed.
)

echo.
echo ✓ Environment ready
echo.
echo Before starting the app:
echo 1. Make sure Ollama is running: ollama serve
echo 2. Ensure Qwen2.5 model is available: ollama pull qwen2.5
echo.
echo Starting Streamlit app...
echo.

REM Launch Streamlit
streamlit run app.py

pause
