#!/bin/bash
# Resume Screening System - Unix/Mac Launch Script

echo ""
echo "========================================"
echo "Resume Screening & Ranking System"
echo "========================================"
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Virtual environment created."
fi

# Activate venv
source venv/bin/activate

# Check if dependencies installed
pip show streamlit > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    echo "Dependencies installed."
fi

echo ""
echo "✓ Environment ready"
echo ""
echo "Before starting the app:"
echo "1. Make sure Ollama is running: ollama serve"
echo "2. Ensure Qwen2.5 model is available: ollama pull qwen2.5"
echo ""
echo "Starting Streamlit app..."
echo ""

# Launch Streamlit
streamlit run app.py
