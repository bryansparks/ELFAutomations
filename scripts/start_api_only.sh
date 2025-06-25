#!/bin/bash
# Start just the Control Center API server

echo "Starting Control Center API Server"
echo "================================="
echo ""

# Check if we're in the right directory
if [ ! -f "elf_automations/api/control_center_minimal.py" ]; then
    echo "Error: Must run from ELFAutomations root directory"
    exit 1
fi

# Check if already running
if lsof -Pi :8001 -sTCP:LISTEN -t >/dev/null ; then
    echo "API server is already running on port 8001"
    echo "PID: $(lsof -Pi :8001 -sTCP:LISTEN -t)"
    exit 0
fi

# Start API server
echo "Starting API server on http://localhost:8001..."
cd elf_automations/api

# Run with proper Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/../.."

# Run the server using uvicorn module
cd ../..
python -m uvicorn elf_automations.api.control_center_minimal:app --host 0.0.0.0 --port 8001
