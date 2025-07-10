#!/bin/bash

# Project Structure Cleanup Script
# Usage: ./cleanup_project.sh [--dry-run]

DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "🔍 DRY RUN MODE - No files will be moved"
fi

echo "🧹 ELFAutomations Project Cleanup"
echo "================================"

# Function to safely create directory
create_dir() {
    if [ ! -d "$1" ]; then
        if [ "$DRY_RUN" = true ]; then
            echo "Would create: $1"
        else
            mkdir -p "$1"
            echo "✅ Created: $1"
        fi
    fi
}

# Function to safely move file
move_file() {
    if [ -f "$1" ]; then
        if [ "$DRY_RUN" = true ]; then
            echo "Would move: $1 → $2"
        else
            mv "$1" "$2"
            echo "📦 Moved: $1 → $2"
        fi
    fi
}

# Function to safely move directory
move_dir() {
    if [ -d "$1" ] && [ ! -d "$2" ]; then
        if [ "$DRY_RUN" = true ]; then
            echo "Would move directory: $1 → $2"
        else
            mv "$1" "$2"
            echo "📁 Moved: $1 → $2"
        fi
    fi
}

echo
echo "📁 Creating new directory structure..."

# Create main directories
create_dir "src"
create_dir "src/elf_automations"
create_dir "src/teams"
create_dir "src/mcps"

create_dir "infrastructure"
create_dir "infrastructure/k8s"
create_dir "infrastructure/docker"
create_dir "infrastructure/terraform"

create_dir "scripts/setup"
create_dir "scripts/deployment"
create_dir "scripts/testing"
create_dir "scripts/utilities"
create_dir "scripts/demos"

create_dir "database"
create_dir "database/schemas"
create_dir "database/migrations"
create_dir "database/seeds"

create_dir "docs/architecture"
create_dir "docs/guides"
create_dir "docs/api"
create_dir "docs/sessions"
create_dir "docs/planning"

create_dir "tests"
create_dir "tests/unit"
create_dir "tests/integration"

create_dir "archive"
create_dir "archive/old_scripts"
create_dir "archive/old_docs"

echo
echo "🚚 Moving files to organized locations..."

# Move session notes to docs/sessions
for file in SESSION*.md; do
    move_file "$file" "docs/sessions/"
done

# Move SQL files to database
for file in *.sql; do
    move_file "$file" "database/schemas/"
done

# Move SQL files from sql/ directory
if [ -d "sql" ]; then
    for file in sql/*.sql; do
        if [[ "$file" == *"create_"* ]]; then
            move_file "$file" "database/schemas/"
        elif [[ "$file" == *"migrate"* ]]; then
            move_file "$file" "database/migrations/"
        else
            move_file "$file" "database/"
        fi
    done
fi

# Organize scripts
if [ -d "scripts" ]; then
    # Setup scripts
    for file in scripts/setup_*.{py,sh}; do
        move_file "$file" "scripts/setup/"
    done

    # Test scripts
    for file in scripts/test_*.{py,sh}; do
        move_file "$file" "scripts/testing/"
    done

    # Deployment scripts
    for file in scripts/deploy_*.{py,sh} scripts/transfer_*.sh; do
        move_file "$file" "scripts/deployment/"
    done

    # Demo scripts
    for file in scripts/demo_*.{py,sh}; do
        move_file "$file" "scripts/demos/"
    done
fi

# Move root level test files
for file in test_*.py check_*.sh debug_*.sh; do
    move_file "$file" "scripts/testing/"
done

# Move documentation files
move_file "AUTONOMY_PROGRESS_CHECKPOINT.md" "docs/planning/"
move_file "N8N_INTEGRATION_PHASE1_COMPLETE.md" "docs/guides/"
move_file "N8N_QUICK_REFERENCE.md" "docs/guides/"
move_file "MCP_FACTORY_UI_UPDATE_MEMORY.md" "docs/sessions/"
move_file "ELF_UI_TEMPLATE_MEMORY.md" "docs/sessions/"
move_file "ELF_UI_SYSTEM_STATUS.md" "docs/sessions/"
move_file "PRECOMMIT_FIX_GUIDE.md" "docs/guides/"
move_file "PROJECT_STRUCTURE.md" "docs/architecture/"
move_file "CLEANUP_PLAN.md" "docs/planning/"

# Move infrastructure files
if [ -d "k8s" ]; then
    move_dir "k8s" "infrastructure/k8s"
fi

# Move old/backup files to archive
for file in *_backup* *_old* *.bak; do
    move_file "$file" "archive/"
done

# Move example files
create_dir "examples/workflows"
create_dir "examples/configs"
for file in examples/*.json; do
    if [[ "$file" == *"workflow"* ]]; then
        move_file "$file" "examples/workflows/"
    else
        move_file "$file" "examples/configs/"
    fi
done

echo
echo "📝 Creating PROJECT_STRUCTURE.md..."

if [ "$DRY_RUN" = false ]; then
    cat > PROJECT_STRUCTURE.md << 'EOF'
# ELFAutomations Project Structure

## Directory Layout

```
ELFAutomations/
├── src/                    # Main source code
│   ├── elf_automations/    # Core Python package
│   ├── teams/             # AI team implementations
│   └── mcps/              # MCP servers
│
├── infrastructure/         # Deployment and configuration
│   ├── k8s/               # Kubernetes manifests
│   ├── docker/            # Dockerfiles
│   └── terraform/         # Infrastructure as Code
│
├── scripts/               # Organized operational scripts
│   ├── setup/             # Installation and setup
│   ├── deployment/        # Deployment scripts
│   ├── testing/           # Test scripts
│   ├── utilities/         # Helper utilities
│   └── demos/             # Demo scripts
│
├── database/              # Database related files
│   ├── schemas/           # Current schema definitions
│   ├── migrations/        # Migration scripts
│   └── seeds/             # Seed data
│
├── docs/                  # Documentation
│   ├── architecture/      # System design docs
│   ├── guides/            # How-to guides
│   ├── api/               # API documentation
│   ├── sessions/          # Development session notes
│   └── planning/          # Planning documents
│
├── tests/                 # Test files
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
│
├── tools/                 # Development tools
├── examples/              # Example configurations
└── archive/               # Deprecated/old files
```

## Key Files Locations

- Python source: `src/elf_automations/`
- Team definitions: `src/teams/`
- MCP servers: `src/mcps/`
- Kubernetes configs: `infrastructure/k8s/`
- Database schemas: `database/schemas/`
- Setup instructions: `docs/guides/`
- Session notes: `docs/sessions/`

## Migration Notes

Files have been reorganized from the flat structure to this hierarchical layout.
Update your import paths and script references accordingly.
EOF
fi

echo
echo "🔧 Updating .gitignore..."

if [ "$DRY_RUN" = false ]; then
    # Add archive directory to gitignore
    echo -e "\n# Archive directory\narchive/\n" >> .gitignore
fi

echo
echo "✨ Cleanup complete!"
echo
echo "⚠️  Important next steps:"
echo "1. Update import paths in Python files"
echo "2. Update script references in documentation"
echo "3. Test that everything still works"
echo "4. Commit changes in logical groups"
echo
echo "💡 Tip: Keep the archive/ directory for 30 days before deleting"
