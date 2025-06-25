'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'
import {
  Home,
  Users,
  Workflow,
  DollarSign,
  Network,
  Settings,
  Command,
  ChevronLeft,
  ChevronRight,
  Brain,
  Shield,
  Activity,
  Package
} from 'lucide-react'
import { useState } from 'react'

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Resources', href: '/resources', icon: Package },
  { name: 'Teams', href: '/teams', icon: Users },
  { name: 'Workflows', href: '/workflows', icon: Workflow },
  { name: 'MCPs', href: '/mcps', icon: Network },
  { name: 'Cost Center', href: '/costs', icon: DollarSign },
  { name: 'Communications', href: '/communications', icon: Brain },
  { name: 'Security', href: '/security', icon: Shield },
  { name: 'Health', href: '/health', icon: Activity },
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
      {/* Header */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-border">
        {!collapsed && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex items-center gap-2"
          >
            <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-elf-500 to-purple-500 flex items-center justify-center">
              <Command className="h-5 w-5 text-white" />
            </div>
            <span className="font-semibold text-gradient">ELF Control</span>
          </motion.div>
        )}

        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1.5 hover:bg-accent rounded-md transition-colors"
        >
          {collapsed ? (
            <ChevronRight className="h-5 w-5" />
          ) : (
            <ChevronLeft className="h-5 w-5" />
          )}
        </button>
      </div>

      {/* Navigation Items */}
      <div className="flex-1 py-4">
        <ul className="space-y-1 px-2">
          {navigation.map((item) => {
            const isActive = pathname === item.href

            return (
              <li key={item.name}>
                <Link
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2 rounded-lg transition-all",
                    "hover:bg-accent hover:text-accent-foreground",
                    isActive && "bg-primary text-primary-foreground hover:bg-primary/90"
                  )}
                >
                  <item.icon className="h-5 w-5 flex-shrink-0" />
                  {!collapsed && (
                    <motion.span
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -10 }}
                      className="text-sm font-medium"
                    >
                      {item.name}
                    </motion.span>
                  )}

                  {isActive && !collapsed && (
                    <motion.div
                      layoutId="activeIndicator"
                      className="ml-auto h-2 w-2 rounded-full bg-white"
                    />
                  )}
                </Link>
              </li>
            )
          })}
        </ul>
      </div>

      {/* Footer */}
      <div className="border-t border-border p-4">
        <div className={cn(
          "flex items-center gap-3",
          collapsed && "justify-center"
        )}>
          <div className="h-8 w-8 rounded-full bg-gradient-to-br from-elf-400 to-purple-400 flex-shrink-0" />
          {!collapsed && (
            <div className="text-sm">
              <p className="font-medium">Admin User</p>
              <p className="text-muted-foreground">admin@elf.ai</p>
            </div>
          )}
        </div>
      </div>
    </motion.nav>
  )
}
