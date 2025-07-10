#!/bin/bash

echo "🔍 Checking staged files for potential secrets..."
echo

# Show what's being detected
echo "Matches found:"
git diff --cached | grep -n -E "sk-[a-zA-Z0-9]{48}|api[_-]?key|secret|password" | head -20

echo
echo "Files with matches:"
git diff --cached --name-only | while read -r file; do
    if git diff --cached -- "$file" | grep -q -E "sk-[a-zA-Z0-9]{48}|api[_-]?key|secret|password"; then
        echo "  - $file"
    fi
done

echo
echo "Context around matches:"
git diff --cached | grep -B2 -A2 -E "sk-[a-zA-Z0-9]{48}|api[_-]?key|secret|password" | head -30
