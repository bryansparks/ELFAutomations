#!/bin/bash

# Fix common import issues in ELF Control Center

echo "🔧 Fixing common import issues..."

# Ensure tsconfig has path mappings
if ! grep -q '"@/\*"' tsconfig.json; then
  echo "❌ tsconfig.json missing path mappings"
  echo "Add this to compilerOptions:"
  echo '  "baseUrl": ".",'
  echo '  "paths": {'
  echo '    "@/*": ["./src/*"]'
  echo '  }'
fi

# Check for missing dependencies
MISSING_DEPS=""
if ! grep -q "framer-motion" package.json; then
  MISSING_DEPS="$MISSING_DEPS framer-motion"
fi
if ! grep -q "tailwindcss-animate" package.json; then
  MISSING_DEPS="$MISSING_DEPS tailwindcss-animate"
fi

if [ ! -z "$MISSING_DEPS" ]; then
  echo "📦 Installing missing dependencies: $MISSING_DEPS"
  npm install $MISSING_DEPS
fi

# Ensure configs exist
if [ ! -f "tailwind.config.js" ]; then
  echo "❌ Missing tailwind.config.js"
fi

if [ ! -f "postcss.config.js" ]; then
  echo "❌ Missing postcss.config.js"
fi

echo "✅ Import check complete!"
echo ""
echo "If you still have issues:"
echo "1. Clear Next.js cache: rm -rf .next"
echo "2. Restart dev server"
echo "3. Check that all components are exported from @elf/ui"
