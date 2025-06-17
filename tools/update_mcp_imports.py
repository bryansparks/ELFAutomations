#!/usr/bin/env python3
"""Update imports in MCP servers after directory consolidation."""

import os
import re
from pathlib import Path

def update_imports_in_file(file_path):
    """Update imports in a single file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Update imports from '../shared/' to '../../shared/'
    updated = content.replace(
        "from '../shared/base-server.js'",
        "from '../../shared/base-server.js'"
    )
    
    if updated != content:
        with open(file_path, 'w') as f:
            f.write(updated)
        print(f"Updated imports in: {file_path}")

def main():
    """Update all TypeScript MCP server imports."""
    mcp_dir = Path("/Users/bryansparks/projects/ELFAutomations/mcp/typescript/servers")
    
    # Find all server.ts files
    for server_dir in mcp_dir.iterdir():
        if server_dir.is_dir():
            server_file = server_dir / "server.ts"
            if server_file.exists():
                update_imports_in_file(server_file)
    
    print("Import updates complete!")

if __name__ == "__main__":
    main()