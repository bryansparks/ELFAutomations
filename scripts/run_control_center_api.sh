#!/bin/bash
# Run the Control Center API Server
# This should run on the DEVELOPMENT machine where Python scripts are available

echo "Starting ElfAutomations Control Center API Server..."
echo "=============================================="
echo ""
echo "This API server provides:"
echo "- MCP discovery (searches npm, GitHub, etc.)"
echo "- MCP installation (runs mcp_marketplace.py)"
echo "- Team management (via Supabase)"
echo "- Cost tracking and system status"
echo ""
echo "The API will be available at:"
echo "- http://localhost:8001 (local)"
echo "- http://$(hostname -I | awk '{print $1}'):8001 (network)"
echo ""
echo "Make sure to update the Control Center UI's .env.local with:"
echo "NEXT_PUBLIC_API_URL=http://$(hostname -I | awk '{print $1}'):8001"
echo ""
echo "=============================================="
echo ""

# Check if we're in the right directory
if [ ! -f "elf_automations/api/control_center_minimal.py" ]; then
    echo "Error: Must run from ELFAutomations root directory"
    exit 1
fi

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check for required environment variables
if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_ANON_KEY" ]; then
    echo "Warning: SUPABASE_URL and SUPABASE_ANON_KEY should be set in .env"
fi

# Run the API server
echo "Starting API server..."
cd elf_automations/api
python control_center_minimal.py
