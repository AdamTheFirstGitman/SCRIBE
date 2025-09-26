#!/bin/bash
# SCRIBE Backend Build Script for Render.com

echo "🚀 Starting SCRIBE Backend Build..."

# Set Python version
echo "📦 Using Python 3.11..."
python --version

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Verify critical imports
echo "🔍 Verifying critical dependencies..."
python -c "
try:
    import fastapi
    import uvicorn
    import supabase
    import anthropic
    import openai
    print('✅ All critical dependencies installed successfully')
except ImportError as e:
    print(f'❌ Missing dependency: {e}')
    exit(1)
"

# Check environment variables
echo "🔐 Checking environment variables..."
python -c "
import os
required_vars = [
    'SUPABASE_URL', 'SUPABASE_SERVICE_KEY',
    'CLAUDE_API_KEY', 'OPENAI_API_KEY'
]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    print(f'❌ Missing environment variables: {missing_vars}')
    exit(1)
else:
    print('✅ All required environment variables present')
"

echo "✅ Backend build completed successfully!"