#!/bin/bash

# QUICK COMMIT - Bypass all pre-commit hooks
# Usage: ./QUICK_COMMIT.sh "Your commit message"

if [ -z "$1" ]; then
    echo "Usage: ./QUICK_COMMIT.sh \"Your commit message\""
    echo
    echo "Example: ./QUICK_COMMIT.sh \"feat: Add N8N integration phase 1\""
    exit 1
fi

echo "Committing with message: $1"
echo

# Add all changes
git add -A

# Commit without pre-commit hooks
git commit --no-verify -m "$1"

# Push to remote
git push

echo
echo "✅ Commit and push complete!"