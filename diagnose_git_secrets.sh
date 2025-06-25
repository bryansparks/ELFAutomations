#!/bin/bash

echo "=== Git Secret Diagnostic ==="
echo

echo "1. Checking if .env.local exists in working directory:"
if [ -f "packages/templates/elf-control-center/.env.local" ]; then
    echo "   ❌ File exists! Delete it with: rm packages/templates/elf-control-center/.env.local"
else
    echo "   ✅ File not found in working directory"
fi

echo
echo "2. Checking if file is tracked by Git:"
if git ls-files | grep -q ".env.local"; then
    echo "   ❌ File is tracked! Remove with: git rm --cached packages/templates/elf-control-center/.env.local"
else
    echo "   ✅ File not tracked"
fi

echo
echo "3. Checking commits with .env.local:"
COMMITS=$(git log --all --pretty=format:%H -- packages/templates/elf-control-center/.env.local)
if [ -n "$COMMITS" ]; then
    echo "   ❌ Found in commits:"
    git log --all --oneline -- packages/templates/elf-control-center/.env.local | head -5
else
    echo "   ✅ Not found in any commits"
fi

echo
echo "4. Checking if problematic commit 1086e236 is in history:"
if git log --oneline | grep -q "1086e236"; then
    echo "   ❌ Commit 1086e236 found in history"
    git log --oneline | grep "1086e236"
else
    echo "   ✅ Commit 1086e236 not in current branch"
fi

echo
echo "5. Checking for secrets in staged files:"
if git diff --cached | grep -q "sk-ant-api03\|sk-proj-"; then
    echo "   ❌ Secrets found in staged files!"
else
    echo "   ✅ No secrets in staged files"
fi

echo
echo "6. Suggested fix:"
if git log --oneline | grep -q "1086e236"; then
    echo "   Run: git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch packages/templates/elf-control-center/.env.local' --prune-empty --tag-name-filter cat -- --all"
    echo "   Then: git push --force origin main"
else
    echo "   Your local history looks clean. Try: git push --force origin main"
fi
