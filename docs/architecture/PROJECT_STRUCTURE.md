# ELFAutomations Project Structure

## Overview
This document describes the organized structure of the ELFAutomations project after cleanup and reorganization.

## Directory Structure

```
ELFAutomations/
├── README.md                    # Main project documentation
├── PROJECT_STRUCTURE.md         # This file
├── CLAUDE.md                    # Project instructions for Claude
├── .gitignore                   # Git ignore patterns
├── pyproject.toml              # Python project configuration
├── requirements.txt            # Python dependencies
├── setup.py                    # Python package setup
│
├── docs/                       # All documentation
│   ├── sessions/              # Session notes and memory files
│   ├── guides/                # How-to guides and tutorials
│   ├── architecture/          # System design and architecture docs
│   └── archive/               # Deprecated or old documentation
│
├── elf_automations/           # Main Python package
│   ├── __init__.py
│   ├── api/                   # API endpoints
│   ├── shared/                # Shared utilities and components
│   └── ...                    # Other package modules
│
├── scripts/                   # Executable scripts
│   ├── setup/                 # Installation and setup scripts
│   ├── testing/               # Test execution scripts
│   ├── deployment/            # Deployment and CI/CD scripts
│   ├── monitoring/            # Health checks and monitoring
│   ├── database/              # Database management scripts
│   └── utilities/             # General utility scripts
│
├── sql/                       # SQL files
│   ├── schemas/               # Table definitions and schemas
│   ├── migrations/            # Database migrations
│   ├── fixes/                 # One-off fixes and patches
│   └── utilities/             # Helper queries and diagnostics
│
├── tests/                     # Test suite
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── e2e/                   # End-to-end tests
│
├── teams/                     # Team configurations
│   └── {team-name}/           # Individual team directories
│
├── mcp/                       # Model Context Protocol servers
│   ├── internal/              # Internal MCP servers
│   └── external/              # External MCP integrations
│
├── k8s/                       # Kubernetes manifests
│   ├── base/                  # Base configurations
│   ├── teams/                 # Team deployments
│   └── infrastructure/        # Infrastructure components
│
├── config/                    # Configuration files
│   ├── agentgateway/          # AgentGateway configs
│   └── ...                    # Other configurations
│
├── examples/                  # Example code and workflows
├── tools/                     # Development tools
└── archive/                   # Archived/old code
```

## Key Changes Made

### 1. Documentation Organization
- Moved all `SESSION_*`, `MEMORY_*`, and checkpoint files to `docs/sessions/`
- Organized documentation by type (guides, architecture, sessions)
- Created archive for deprecated docs

### 2. Scripts Categorization
- **setup/**: All installation and setup scripts
- **testing/**: Test execution and validation scripts
- **deployment/**: CI/CD and deployment scripts
- **monitoring/**: Health checks and status scripts
- **database/**: Database-specific operations
- **utilities/**: General purpose scripts

### 3. SQL Organization
- **schemas/**: Core table definitions
- **migrations/**: Version-controlled migrations
- **fixes/**: One-off fixes and patches
- **utilities/**: Helper queries and diagnostics

### 4. Test Consolidation
- Moved all `test_*.py` files from root to `tests/`
- Ready for further organization into unit/integration/e2e

### 5. Cleanup Actions
- Removed temporary files and backups
- Updated `.gitignore` with comprehensive patterns
- Consolidated duplicate directories

## Migration Notes

### For Developers
1. Update any hardcoded paths in scripts that reference moved files
2. Check import statements in Python files
3. Update CI/CD pipelines if they reference specific file locations

### Common Path Updates
- Session files: `/` → `/docs/sessions/`
- Test files: `/test_*.py` → `/tests/test_*.py`
- Setup scripts: `/scripts/setup_*.py` → `/scripts/setup/setup_*.py`
- SQL schemas: `/sql/create_*.sql` → `/sql/schemas/create_*.sql`

## Benefits
1. **Improved Navigation**: Clear, logical structure
2. **Better Organization**: Related files grouped together
3. **Easier Maintenance**: Consistent patterns
4. **Cleaner Git History**: Less clutter in commits
5. **Faster Onboarding**: New developers understand layout

## Next Steps
1. Run the cleanup script: `python scripts/cleanup_project_structure.py`
2. Review moved files and update any broken references
3. Commit changes in logical groups
4. Update documentation references
