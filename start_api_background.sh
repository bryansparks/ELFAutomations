#!/bin/bash
cd /Users/bryansparks/projects/ELFAutomations
nohup python -m uvicorn elf_automations.api.control_center_minimal:app --host 0.0.0.0 --port 8001 > api_server.log 2>&1 &
echo "API server started in background. PID: $!"
echo "Check logs: tail -f api_server.log"
