#!/bin/bash
# SCRIBE Backend - Local Development Server
# Uses venv to avoid conflicts with system Python

echo "🚀 Starting SCRIBE Backend..."
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ venv not found. Creating it..."
    python3 -m venv venv
    ./venv/bin/pip install --upgrade pip
    ./venv/bin/pip install -r requirements.txt
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "Please create .env with required variables (see .env.example)"
    exit 1
fi

echo "✅ Environment ready"
echo ""
echo "📡 Backend will run on: http://127.0.0.1:8000"
echo "📚 API Docs: http://127.0.0.1:8000/docs"
echo ""
echo "Press CTRL+C to stop"
echo ""

# Run uvicorn with venv Python
./venv/bin/uvicorn main:app --reload --host 127.0.0.1 --port 8000
