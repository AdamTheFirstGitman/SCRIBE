#!/bin/bash
# SCRIBE Frontend - Local Development Server

echo "🚀 Starting SCRIBE Frontend..."
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "❌ node_modules not found. Installing dependencies..."
    npm install
fi

# Create .env.local if it doesn't exist
if [ ! -f ".env.local" ]; then
    echo "📝 Creating .env.local for local development..."
    echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
    echo "✅ .env.local created"
fi

echo "✅ Environment ready"
echo ""
echo "🌐 Frontend will run on: http://localhost:3000"
echo "🔗 API Backend: $(cat .env.local | grep NEXT_PUBLIC_API_URL | cut -d= -f2)"
echo ""
echo "Press CTRL+C to stop"
echo ""

# Run Next.js dev server
npm run dev
