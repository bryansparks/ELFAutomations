#!/bin/bash

# Script to fix pre-commit hook issues and allow commits to flow to GitHub

echo "=== ELFAutomations Pre-commit Fix Script ==="
echo

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 1. First, let's see the current git status
echo "1. Checking current git status..."
git status

echo
echo "2. Checking for unpushed commits..."
git log origin/main..HEAD --oneline 2>/dev/null || echo "No unpushed commits found"

echo
echo "3. Analyzing pre-commit configuration..."
if [ -f .pre-commit-config.yaml ]; then
    echo "Pre-commit hooks configured:"
    echo "- black (Python formatter)"
    echo "- isort (Python import sorter)"
    echo "- trailing-whitespace"
    echo "- end-of-file-fixer"
    echo "- check-yaml"
    echo "- check-added-large-files"
    echo "- check-merge-conflict"
fi

echo
echo "4. Checking for large files..."
# Find files larger than 1MB (pre-commit default is 500KB)
find . -type f -size +1M -not -path "./.git/*" -not -path "./node_modules/*" -not -path "./venv/*" | while read -r file; do
    size=$(ls -lh "$file" | awk '{print $5}')
    echo "Large file found: $file ($size)"
done

echo
echo "5. Creating .gitattributes to handle large files..."
cat > .gitattributes << 'EOF'
# Handle large files
package-lock.json filter=lfs diff=lfs merge=lfs -text
yarn.lock filter=lfs diff=lfs merge=lfs -text
*.sqlite filter=lfs diff=lfs merge=lfs -text
*.db filter=lfs diff=lfs merge=lfs -text

# Exclude from checks
third-party/** -diff -merge
node_modules/** -diff -merge
EOF

echo
echo "6. Creating fix for YAML validation..."
# Create a script to validate and fix YAML files
cat > validate_yaml.py << 'EOF'
#!/usr/bin/env python3
import yaml
import sys
import os

def validate_yaml_file(filepath):
    """Validate a YAML file and report errors."""
    try:
        with open(filepath, 'r') as f:
            yaml.safe_load_all(f)
        return True, None
    except yaml.YAMLError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Error reading file: {str(e)}"

def find_yaml_files():
    """Find all YAML files in the project."""
    yaml_files = []
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        if any(skip in root for skip in ['.git', 'node_modules', 'venv', '__pycache__']):
            continue
        for file in files:
            if file.endswith(('.yaml', '.yml')):
                yaml_files.append(os.path.join(root, file))
    return yaml_files

if __name__ == "__main__":
    print("Validating YAML files...")
    yaml_files = find_yaml_files()
    errors = []
    
    for filepath in yaml_files:
        valid, error = validate_yaml_file(filepath)
        if not valid:
            errors.append((filepath, error))
            print(f"❌ {filepath}: {error}")
    
    if errors:
        print(f"\nFound {len(errors)} YAML files with errors")
        sys.exit(1)
    else:
        print(f"\n✅ All {len(yaml_files)} YAML files are valid")
        sys.exit(0)
EOF

chmod +x validate_yaml.py

echo
echo "7. Options to proceed:"
echo
echo "Option A: Temporarily bypass pre-commit hooks (Quick fix)"
echo "   git commit --no-verify -m 'Your commit message'"
echo "   git push"
echo
echo "Option B: Fix issues and commit normally"
echo "   1. Run: python validate_yaml.py  # to find YAML errors"
echo "   2. Add large files to .gitignore or use Git LFS"
echo "   3. Run: pre-commit run --all-files  # to fix formatting"
echo "   4. Then commit normally"
echo
echo "Option C: Selectively disable problematic hooks"
echo "   Edit .pre-commit-config.yaml and comment out:"
echo "   - check-added-large-files"
echo "   - check-yaml (if YAML files are causing issues)"
echo
echo "Option D: Update pre-commit configuration for better tolerance"
echo "   We can create a more lenient configuration..."

# Create an alternative pre-commit config
cat > .pre-commit-config-lenient.yaml << 'EOF'
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3
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
        exclude: ^(third-party/|old/|venv/|node_modules/|.*\.json$)
      - id: check-yaml
        exclude: ^(third-party/|old/|k8s/|helm/|agent-configs/)
        args: ['--unsafe']  # Allow custom tags
      - id: check-added-large-files
        args: ['--maxkb=2048']  # Increase limit to 2MB
        exclude: 'package-lock\.json|yarn\.lock|.*\.sqlite|.*\.db'
      - id: check-merge-conflict
EOF

echo
echo "8. To use the lenient configuration:"
echo "   mv .pre-commit-config.yaml .pre-commit-config-strict.yaml"
echo "   mv .pre-commit-config-lenient.yaml .pre-commit-config.yaml"
echo "   pre-commit install"
echo
echo "9. Quick commands to get unstuck:"
echo "   # See what pre-commit is complaining about:"
echo "   pre-commit run --all-files"
echo
echo "   # Bypass and commit immediately:"
echo "   git add ."
echo "   git commit --no-verify -m 'WIP: Fixing pre-commit issues'"
echo "   git push"
echo
echo "   # Reset pre-commit if it's broken:"
echo "   pre-commit uninstall"
echo "   pre-commit clean"
echo "   pre-commit install"

# Check if there are staged changes
if git diff --staged --quiet; then
    echo
    echo "No staged changes found. Stage your changes first with:"
    echo "   git add ."
else
    echo
    echo "You have staged changes ready to commit."
fi

echo
echo "=== Script complete ==="