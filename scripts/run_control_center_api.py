#!/usr/bin/env python3
"""
Run the Control Center API server
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

if __name__ == "__main__":
    # Set up environment
    os.environ["PYTHONPATH"] = str(Path(__file__).parent.parent)

    # Run the API server
    import uvicorn

    from elf_automations.api.control_center_minimal import app

    print("🚀 Starting ElfAutomations Control Center API...")
    print("📍 API will be available at: http://localhost:8001")
    print("📚 API docs available at: http://localhost:8001/docs")
    print("🔄 WebSocket endpoint at: ws://localhost:8001/ws")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info",
    )
