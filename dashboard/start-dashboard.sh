#!/bin/bash

# ELF Automations Dashboard Startup Script

echo "🚀 Starting ELF Automations Dashboard..."

# Check if we're in the dashboard directory
if [ ! -f "README.md" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: This script must be run from the dashboard directory"
    exit 1
fi

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "❌ Port $1 is already in use"
        return 1
    fi
    return 0
}

# Check required ports
echo "🔍 Checking port availability..."
if ! check_port 8000; then
    echo "Backend port 8000 is in use. Please stop the existing service."
    exit 1
fi

if ! check_port 3001; then
    echo "Frontend port 3001 is in use. Please stop the existing service."
    exit 1
fi

# Start backend
echo "🔧 Starting backend API server..."
cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
source venv/bin/activate
echo "📦 Installing backend dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

# Check for required environment variables
if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_ANON_KEY" ]; then
    echo "⚠️  Warning: Supabase credentials not set. Some features may not work."
    echo "   Set SUPABASE_URL and SUPABASE_ANON_KEY environment variables."
fi

# Start backend in background
echo "🚀 Starting backend on http://localhost:8000"
python main.py &
BACKEND_PID=$!
cd ..

# Give backend time to start
sleep 3

# Start frontend
echo "🎨 Starting frontend application..."
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

# Start frontend
echo "🚀 Starting frontend on http://localhost:3001"
npm run dev &
FRONTEND_PID=$!
cd ..

# Function to cleanup on exit
cleanup() {
    echo -e "\n🛑 Shutting down dashboard..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up trap for cleanup
trap cleanup INT TERM

# Wait and show status
echo -e "\n✅ ELF Dashboard is running!"
echo "   Backend API: http://localhost:8000"
echo "   Frontend UI: http://localhost:3001"
echo "   API Docs: http://localhost:8000/docs"
echo -e "\nPress Ctrl+C to stop the dashboard\n"

# Keep script running
wait
