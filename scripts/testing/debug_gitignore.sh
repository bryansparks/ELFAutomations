#!/bin/bash

echo "🔍 Debugging .gitignore for .env files"
echo

# Find all .env files
echo "All .env files found:"
find . -name "*.env*" -not -path "./.git/*" -type f | while read -r file; do
    echo -n "  $file - "
    if git check-ignore "$file" > /dev/null 2>&1; then
        echo "✅ IGNORED"
    else
        echo "❌ NOT IGNORED"
    fi
done

echo
echo "Testing specific patterns:"
test_files=(".env" ".env.template" ".env.local" "subfolder/.env")

for test_file in "${test_files[@]}"; do
    echo -n "  $test_file: "
    if git check-ignore "$test_file" 2>/dev/null; then
        echo "would be ignored"
    else
        echo "would NOT be ignored"
    fi
done

echo
echo "Current .gitignore rules for .env:"
grep -n "\.env" .gitignore || echo "No .env rules found!"
