#!/bin/bash
# Check status of Control Center services

echo "Control Center Service Status"
echo "============================="
echo ""

# Check API server
echo "API Server (port 8001):"
if lsof -Pi :8001 -sTCP:LISTEN -t >/dev/null ; then
    PID=$(lsof -Pi :8001 -sTCP:LISTEN -t)
    echo "  ✓ Running (PID: $PID)"
    # Try to check if it's healthy
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo "  ✓ Responding to health checks"
    else
        echo "  ✗ Not responding to health checks"
    fi
else
    echo "  ✗ Not running"
fi

echo ""

# Check UI
echo "UI Server (port 3002):"
if lsof -Pi :3002 -sTCP:LISTEN -t >/dev/null ; then
    PID=$(lsof -Pi :3002 -sTCP:LISTEN -t)
    echo "  ✓ Running (PID: $PID)"
    # Try to check if it's responding
    if curl -s http://localhost:3002 > /dev/null 2>&1; then
        echo "  ✓ Responding to requests"
    else
        echo "  ✗ Not responding to requests"
    fi
else
    echo "  ✗ Not running"
fi

echo ""
echo "============================="
echo ""
echo "Commands:"
echo "  Start both:    ./scripts/run_control_center_local.sh"
echo "  Stop API:      kill $(lsof -Pi :8001 -sTCP:LISTEN -t 2>/dev/null || echo 'N/A')"
echo "  Stop UI:       kill $(lsof -Pi :3002 -sTCP:LISTEN -t 2>/dev/null || echo 'N/A')"
echo ""
