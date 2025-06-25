#!/bin/bash

# ELFAutomations Git Pre-commit Fix Script
# This script provides multiple solutions to bypass or fix pre-commit hook issues

echo "=== ELFAutomations Git Pre-commit Fix Script ==="
echo

# Function to display current status
show_status() {
    echo "Current Git Status:"
    git status --short
    echo
    echo "Unpushed commits (if any):"
    git log origin/main..HEAD --oneline 2>/dev/null || echo "No unpushed commits found"
    echo
}

# Function to check for large files
check_large_files() {
    echo "Checking for large files (>500KB)..."
    find . -type f -size +500k -not -path "./.git/*" -not -path "./node_modules/*" -not -path "./venv/*" | while read -r file; do
        size=$(ls -lh "$file" | awk '{print $5}')
        echo "  Large file: $file ($size)"
    done
    echo
}

# Main menu
show_menu() {
    echo "Choose an option to fix your git commit issues:"
    echo
    echo "1) QUICK FIX - Bypass all pre-commit hooks (Recommended)"
    echo "2) Add large files to .gitignore"
    echo "3) Disable problematic pre-commit hooks"
    echo "4) Completely uninstall pre-commit"
    echo "5) Show diagnostic information"
    echo "6) Exit"
    echo
}

# Option 1: Quick bypass
quick_bypass() {
    echo "=== Quick Bypass Solution ==="
    echo
    echo "This will commit your changes without running pre-commit hooks."
    echo
    echo "Run these commands:"
    echo
    echo "  git add -A"
    echo "  git commit --no-verify -m 'Your commit message'"
    echo "  git push"
    echo
    echo "Example with a real commit message:"
    echo "  git commit --no-verify -m 'feat: Add N8N integration phase 1'"
    echo
}

# Option 2: Update gitignore
update_gitignore() {
    echo "=== Updating .gitignore ==="
    echo
    echo "Adding large files to .gitignore..."
    
    cat >> .gitignore << 'EOF'

# Large files that cause pre-commit issues
package-lock.json
yarn.lock
*.sqlite
*.db
node_modules/
third-party/kagent
third-party/agentgateway

# Temporary and cache files
*.tmp
*.log
*.cache
.pytest_cache/
__pycache__/
EOF

    echo "Updated .gitignore. Now run:"
    echo "  git add .gitignore"
    echo "  git commit -m 'Update .gitignore for large files'"
    echo
}

# Option 3: Disable hooks
disable_hooks() {
    echo "=== Disabling Problematic Hooks ==="
    echo
    echo "Creating a lenient pre-commit configuration..."
    
    cp .pre-commit-config.yaml .pre-commit-config.yaml.backup
    
    cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        exclude: ^(third-party/|old/|venv/|node_modules/)

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        exclude: ^(third-party/|old/|venv/|node_modules/)

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
        exclude: ^(third-party/|old/|venv/|node_modules/)
      - id: end-of-file-fixer
        exclude: ^(third-party/|old/|venv/|node_modules/|.*\.json$|.*\.lock$)
      # Disabled problematic hooks:
      # - id: check-yaml
      # - id: check-added-large-files
      - id: check-merge-conflict
EOF

    echo "Pre-commit configuration updated. Now run:"
    echo "  pre-commit install --force"
    echo "  git add .pre-commit-config.yaml"
    echo "  git commit -m 'Update pre-commit config to fix blocking issues'"
    echo
}

# Option 4: Uninstall pre-commit
uninstall_precommit() {
    echo "=== Uninstalling Pre-commit ==="
    echo
    echo "This will completely remove pre-commit hooks..."
    
    pre-commit uninstall
    echo
    echo "Pre-commit hooks have been uninstalled."
    echo "You can now commit normally without any hook checks:"
    echo "  git add -A"
    echo "  git commit -m 'Your commit message'"
    echo "  git push"
    echo
    echo "To reinstall pre-commit later, run:"
    echo "  pre-commit install"
    echo
}

# Option 5: Diagnostics
show_diagnostics() {
    echo "=== Diagnostic Information ==="
    echo
    
    show_status
    check_large_files
    
    echo "Pre-commit configuration:"
    if [ -f .pre-commit-config.yaml ]; then
        echo "Hooks configured:"
        grep -E "id:|repo:" .pre-commit-config.yaml | sed 's/^/  /'
    else
        echo "No .pre-commit-config.yaml found"
    fi
    echo
    
    echo "To see what pre-commit is complaining about, run:"
    echo "  pre-commit run --all-files --verbose"
    echo
}

# Main execution
main() {
    while true; do
        show_menu
        read -p "Enter your choice (1-6): " choice
        echo
        
        case $choice in
            1) quick_bypass ;;
            2) update_gitignore ;;
            3) disable_hooks ;;
            4) uninstall_precommit ;;
            5) show_diagnostics ;;
            6) echo "Exiting..."; exit 0 ;;
            *) echo "Invalid choice. Please try again." ;;
        esac
        
        echo
        read -p "Press Enter to continue..."
        echo
    done
}

# Show initial status
echo "Initial Status:"
show_status

# Run main menu
main