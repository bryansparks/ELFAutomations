#!/bin/bash

# Check for any .env files that might accidentally get committed

echo "🔍 Checking for .env files..."

# Find all .env files
env_files=$(find . -name "*.env*" -not -path "./.git/*" -not -name "*.example" -not -name "*.template" -type f)

if [ -z "$env_files" ]; then
    echo "✅ No .env files found in repository"
else
    echo "⚠️  Found the following .env files:"
    echo "$env_files" | while read -r file; do
        echo "  - $file"
        # Check if it's in .gitignore
        if git check-ignore "$file" > /dev/null 2>&1; then
            echo "    ✅ (ignored by git)"
        else
            echo "    ❌ NOT IN .GITIGNORE - This file could be committed!"
        fi
    done
    
    echo
    echo "📝 To add these to .gitignore, run:"
    echo "$env_files" | while read -r file; do
        echo "echo '$file' >> .gitignore"
    done
fi

# Check if any .env files are tracked
tracked=$(git ls-files | grep -E "\.env")
if [ -n "$tracked" ]; then
    echo
    echo "❌ CRITICAL: These .env files are tracked by git:"
    echo "$tracked"
    echo
    echo "Remove them with:"
    echo "$tracked" | while read -r file; do
        echo "git rm --cached $file"
    done
fi