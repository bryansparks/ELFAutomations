# ELFAutomations Project Cleanup Plan

## Executive Summary

The ELFAutomations project has grown organically and now needs reorganization for better maintainability. This cleanup will transform a flat, cluttered structure into a well-organized hierarchy without breaking any functionality.

## Current Issues

### 1. Root Directory Clutter
- **25+ miscellaneous files** in root including:
  - Session notes (SESSION*.md)
  - Test scripts (test_*.py, check_*.sh)
  - Configuration files scattered
  - Various utility scripts

### 2. Scripts Directory Chaos
- **120+ scripts** in a single directory
- No categorization by purpose
- Difficult to find specific functionality
- Mix of setup, test, deployment, and utility scripts

### 3. SQL File Proliferation
- **40+ SQL files** with no organization
- Mixed schema definitions and migrations
- Multiple versions of same tables
- No clear versioning strategy

### 4. Documentation Sprawl
- **100+ markdown files** without structure
- Session notes mixed with permanent docs
- No categorization by topic or purpose
- Hard to find relevant documentation

### 5. Source Code Organization
- Multiple MCP server directories
- Teams directory at root level
- No clear separation of source from config

## New Structure Overview

```
ELFAutomations/
├── src/                    # All source code
│   ├── elf_automations/    # Core Python package
│   ├── teams/              # AI team implementations
│   └── mcps/               # MCP servers (consolidated)
├── infrastructure/         # Deployment & configuration
│   ├── k8s/                # Kubernetes manifests
│   ├── docker/             # Dockerfiles
│   └── terraform/          # Infrastructure as Code
├── scripts/                # Organized by purpose
│   ├── setup/              # Installation & setup
│   ├── deployment/         # Deployment scripts
│   ├── testing/            # Test scripts
│   ├── utilities/          # Helper utilities
│   └── demos/              # Demo scripts
├── database/               # All database related
│   ├── schemas/            # Current schemas
│   ├── migrations/         # Version migrations
│   └── seeds/              # Seed data
├── docs/                   # Organized documentation
│   ├── architecture/       # System design
│   ├── guides/             # How-to guides
│   ├── api/                # API documentation
│   ├── sessions/           # Development notes
│   └── planning/           # Planning documents
├── tests/                  # Test suites
├── tools/                  # Development tools
├── examples/               # Example code
└── archive/                # Old/deprecated items
```

## Cleanup Strategy

### Phase 1: Preparation
1. Create full backup of current state
2. Run cleanup script in dry-run mode
3. Review proposed changes
4. Identify any custom path dependencies

### Phase 2: Execution
1. Run the cleanup script
2. Verify file movements
3. Update import paths where needed
4. Test critical functionality

### Phase 3: Validation
1. Run test suites
2. Verify documentation links
3. Check deployment scripts
4. Update CI/CD if needed

## Benefits

1. **Improved Navigation**: Find files quickly with logical organization
2. **Better Onboarding**: New developers understand structure immediately
3. **Easier Maintenance**: Related files grouped together
4. **Cleaner Git History**: Less clutter in commits
5. **Professional Structure**: Follows industry standards

## Risk Mitigation

1. **Full Backup**: Everything moved to archive/ first
2. **Dry Run**: Preview all changes before execution
3. **Migration Log**: Complete record of all file movements
4. **Incremental Updates**: Fix broken paths as found
5. **Rollback Plan**: Archive preserves original structure

## Execution Commands

```bash
# 1. Make scripts executable
chmod +x cleanup_project.sh
chmod +x scripts/cleanup_project_structure.py

# 2. Run dry-run first
./cleanup_project.sh --dry-run
# OR
python scripts/cleanup_project_structure.py --dry-run

# 3. Review output and when ready, execute
./cleanup_project.sh
# OR
python scripts/cleanup_project_structure.py

# 4. Check the migration log
cat migration_log.json
```

## Post-Cleanup Tasks

1. **Update Import Paths**: Search and replace old paths in Python files
2. **Fix Script References**: Update paths in documentation
3. **Update Docker/K8s**: Adjust paths in deployment configs
4. **Test Everything**: Run full test suite
5. **Commit Strategically**: Group related changes in commits

## Timeline

- Preparation: 15 minutes
- Execution: 5 minutes
- Validation: 30 minutes
- Path fixes: 1-2 hours (depending on codebase)

Total estimated time: 2-3 hours

## Notes

- The archive/ directory will be added to .gitignore
- Keep archive/ for at least 30 days before deletion
- All file movements are logged in migration_log.json
- No files are deleted, only moved
