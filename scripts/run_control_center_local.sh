#!/bin/bash
# Run Control Center locally (both API and UI on same machine)

echo "Starting ElfAutomations Control Center (Local Mode)"
echo "=================================================="
echo ""

# Check if we're in the right directory
if [ ! -f "elf_automations/api/control_center_minimal.py" ]; then
    echo "Error: Must run from ELFAutomations root directory"
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo -e "\n\nShutting down services..."
    if [ ! -z "$API_PID" ] && [ -z "$API_ALREADY_RUNNING" ]; then
        kill $API_PID 2>/dev/null
    fi
    if [ ! -z "$UI_PID" ] && [ -z "$UI_ALREADY_RUNNING" ]; then
        kill $UI_PID 2>/dev/null
    fi
    exit
}

trap cleanup EXIT INT TERM

# Check if API is already running
if lsof -Pi :8001 -sTCP:LISTEN -t >/dev/null ; then
    echo "API server is already running on port 8001"
    echo "To restart it, first kill the existing process:"
    echo "  kill $(lsof -Pi :8001 -sTCP:LISTEN -t)"
    API_ALREADY_RUNNING=true
else
    # Start API server in background
    echo "Starting API server on http://localhost:8001..."
    cd elf_automations/api
    python control_center_minimal.py > /tmp/control_center_api.log 2>&1 &
    API_PID=$!
    cd ../..

    # Give API time to start
    sleep 3

    # Check if API is running
    if ! curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo "Warning: API server may not have started properly"
        echo "Check the logs: tail -f /tmp/control_center_api.log"
    else
        echo "API server started successfully"
    fi
fi

# Check if UI is already running
if lsof -Pi :3002 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "\nUI is already running on http://localhost:3002"
    echo "To restart it, first kill the existing process:"
    echo "  kill $(lsof -Pi :3002 -sTCP:LISTEN -t)"
    UI_ALREADY_RUNNING=true
else
    # Start UI
    echo -e "\nStarting UI on http://localhost:3002..."
    cd packages/templates/elf-control-center

    # Check if .env.local exists and has correct URL
    if [ -f ".env.local" ]; then
        if ! grep -q "NEXT_PUBLIC_API_URL=http://localhost:8001" .env.local; then
            echo "Warning: .env.local exists but API URL may not be set to localhost:8001"
        fi
    else
        echo "Creating .env.local with localhost configuration..."
        echo "NEXT_PUBLIC_API_URL=http://localhost:8001" > .env.local
        echo "NEXT_PUBLIC_WS_URL=ws://localhost:8001/ws" >> .env.local
    fi

    # Run Next.js in dev mode for hot reload
    npm run dev > /tmp/control_center_ui.log 2>&1 &
    UI_PID=$!

    sleep 3
    if lsof -Pi :3002 -sTCP:LISTEN -t >/dev/null ; then
        echo "UI started successfully"
    else
        echo "UI failed to start. Check logs: tail -f /tmp/control_center_ui.log"
    fi
fi

echo -e "\n=================================================="
echo "Control Center is running!"
echo ""
echo "UI:  http://localhost:3002"
echo "API: http://localhost:8001"
echo ""
if [ ! -z "$API_ALREADY_RUNNING" ] || [ ! -z "$UI_ALREADY_RUNNING" ]; then
    echo "Note: Some services were already running and weren't restarted."
    echo ""
fi
echo "Logs:"
echo "  API: tail -f /tmp/control_center_api.log"
echo "  UI:  tail -f /tmp/control_center_ui.log"
echo ""
echo "Press Ctrl+C to stop services started by this script"
echo "=================================================="

# Wait for processes we started
if [ ! -z "$API_PID" ] && [ -z "$API_ALREADY_RUNNING" ]; then
    wait $API_PID
fi
if [ ! -z "$UI_PID" ] && [ -z "$UI_ALREADY_RUNNING" ]; then
    wait $UI_PID
fi

# If both were already running, just sleep
if [ ! -z "$API_ALREADY_RUNNING" ] && [ ! -z "$UI_ALREADY_RUNNING" ]; then
    echo -e "\nBoth services are already running. Press Ctrl+C to exit."
    sleep infinity
fi
