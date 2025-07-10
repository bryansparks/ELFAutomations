#!/usr/bin/env python3
"""
Run the Control Center API server - Fixed for new structure
"""

import os
import sys
from pathlib import Path

# Add project root and src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src" / "elf_automations"))

if __name__ == "__main__":
    # Set up environment
    os.environ[
        "PYTHONPATH"
    ] = f"{project_root}:{project_root / 'src' / 'elf_automations'}"

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
