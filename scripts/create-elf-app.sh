#!/bin/bash
# Create a new ELF app from the Control Center template

set -e

# Check if app name was provided
if [ -z "$1" ]; then
    echo "❌ Please provide an app name"
    echo "Usage: ./create-elf-app.sh my-app-name"
    exit 1
fi

APP_NAME=$1
APP_DIR="packages/templates/$APP_NAME"
TEMPLATE_DIR="packages/templates/elf-control-center"

echo "🚀 Creating new ELF app: $APP_NAME"

# Check if template exists
if [ ! -d "$TEMPLATE_DIR" ]; then
    echo "❌ Template directory not found: $TEMPLATE_DIR"
    exit 1
fi

# Check if app already exists
if [ -d "$APP_DIR" ]; then
    echo "❌ App directory already exists: $APP_DIR"
    exit 1
fi

# Copy template
echo "📁 Copying template..."
cp -r "$TEMPLATE_DIR" "$APP_DIR"

# Update package.json
echo "📝 Updating package.json..."
cd "$APP_DIR"
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/elf-control-center/$APP_NAME/g" package.json
else
    # Linux
    sed -i "s/elf-control-center/$APP_NAME/g" package.json
fi

# Remove Control Center specific pages
echo "🧹 Cleaning up template..."
rm -rf src/app/teams src/app/workflows src/app/mcps src/app/costs
rm -rf src/app/communications src/app/security src/app/health
rm -f src/services/api.ts
rm -f src/hooks/useSystemStats.ts

# Create a basic home page
echo "📄 Creating starter pages..."
cat > src/app/page.tsx << 'EOF'
'use client'

import { PageTransition } from '@/components/ui/page-transition'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

export default function HomePage() {
  return (
    <PageTransition variant="fade">
      <div className="p-6 space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gradient">Welcome to Your New App</h1>
          <p className="text-muted-foreground mt-1">
            Built with the ELF UI template system
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <Card variant="glass" hover="lift">
            <CardHeader>
              <CardTitle>Glass Card</CardTitle>
            </CardHeader>
            <CardContent>
              <p>This is a glass morphism card with hover effect.</p>
            </CardContent>
          </Card>

          <Card variant="gradient" hover="glow">
            <CardHeader>
              <CardTitle>Gradient Card</CardTitle>
            </CardHeader>
            <CardContent>
              <p>This card has a gradient background with glow effect.</p>
            </CardContent>
          </Card>

          <Card variant="neu" hover="lift">
            <CardHeader>
              <CardTitle>Neumorphic Card</CardTitle>
            </CardHeader>
            <CardContent>
              <p>This demonstrates the neumorphism style.</p>
            </CardContent>
          </Card>
        </div>

        <div className="flex gap-4">
          <Button variant="default">Default Button</Button>
          <Button variant="gradient">Gradient Button</Button>
          <Button variant="outline">Outline Button</Button>
          <Button variant="glow">Glow Button</Button>
        </div>
      </div>
    </PageTransition>
  )
}
EOF

# Update navigation
cat > src/components/navigation.tsx << 'EOF'
'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'
import { Home, Settings, ChevronLeft, ChevronRight } from 'lucide-react'
import { useState } from 'react'

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export function Navigation() {
  const pathname = usePathname()
  const [collapsed, setCollapsed] = useState(false)

  return (
    <motion.nav
      className={cn(
        "relative bg-card border-r border-border transition-all duration-300",
        collapsed ? "w-16" : "w-64"
      )}
      animate={{ width: collapsed ? 64 : 256 }}
    >
      <div className="flex h-16 items-center justify-between px-4 border-b border-border">
        {!collapsed && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <h2 className="text-lg font-semibold text-gradient">Your App</h2>
          </motion.div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1 rounded-md hover:bg-accent"
        >
          {collapsed ? <ChevronRight className="h-5 w-5" /> : <ChevronLeft className="h-5 w-5" />}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto py-4">
        <nav className="space-y-1 px-2">
          {navigation.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  'hover:bg-accent hover:text-accent-foreground',
                  isActive && 'bg-accent text-accent-foreground',
                  collapsed && 'justify-center'
                )}
              >
                <item.icon className="h-5 w-5 flex-shrink-0" />
                {!collapsed && (
                  <motion.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                  >
                    {item.name}
                  </motion.span>
                )}
              </Link>
            )
          })}
        </nav>
      </div>
    </motion.nav>
  )
}
EOF

# Update layout title
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/ElfAutomations.ai Control Center/$APP_NAME/g" src/app/layout.tsx
    sed -i '' "s/Real-time monitoring and control of your autonomous AI ecosystem/Built with ELF UI Template/g" src/app/layout.tsx
else
    sed -i "s/ElfAutomations.ai Control Center/$APP_NAME/g" src/app/layout.tsx
    sed -i "s/Real-time monitoring and control of your autonomous AI ecosystem/Built with ELF UI Template/g" src/app/layout.tsx
fi

echo ""
echo "✅ App created successfully!"
echo ""
echo "To get started:"
echo "  cd $APP_DIR"
echo "  npm install"
echo "  npm run dev"
echo ""
echo "Your app will be available at http://localhost:3000"
echo ""
echo "📚 Available components:"
echo "  - Buttons (default, gradient, outline, glow, glass)"
echo "  - Cards (default, glass, gradient, neu)"
echo "  - MetricCard (for dashboard metrics)"
echo "  - Loading animations (dots, pulse, wave, orbit, morph)"
echo "  - PageTransition (fade, slide, scale)"
echo ""
echo "🎨 Styling utilities:"
echo "  - text-gradient (gradient text)"
echo "  - Dark theme by default"
echo "  - Tailwind CSS with custom ELF colors"
echo ""
echo "Happy coding! 🚀"
