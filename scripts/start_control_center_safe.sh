#!/bin/bash
# Start the ElfAutomations.ai Control Center (Safe Mode - avoids dependency issues)

echo "🚀 Starting ElfAutomations.ai Control Center (Safe Mode)..."
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

# Start the minimal API server in background
echo "📡 Starting Control Center API (Minimal version)..."
cd "$(dirname "$0")/.."
python elf_automations/api/control_center_minimal.py &
API_PID=$!

# Give API time to start
sleep 3

# Check if API is running
if ! curl -s http://localhost:8001/health > /dev/null; then
    echo "❌ API failed to start. Check the logs above."
    exit 1
fi

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
