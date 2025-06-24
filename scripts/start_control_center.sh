#!/bin/bash
# Start the ElfAutomations.ai Control Center

echo "🚀 Starting ElfAutomations.ai Control Center..."
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down Control Center..."
    kill $API_PID $UI_PID 2>/dev/null
    exit 0
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

# Start the API server in background
echo "📡 Starting Control Center API..."
cd "$(dirname "$0")/.."
python scripts/run_control_center_api.py &
API_PID=$!

# Give API time to start
sleep 3

# Start the UI in background
echo "🖥️  Starting Control Center UI..."
cd packages/templates/elf-control-center
npm run dev &
UI_PID=$!

echo ""
echo "✅ Control Center is running!"
echo ""
echo "🌐 UI: http://localhost:3002"
echo "📚 API: http://localhost:8001"
echo "📖 API Docs: http://localhost:8001/docs"
echo ""
echo "Press Ctrl+C to stop..."

# Wait for processes
wait
