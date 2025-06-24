'use client'

import { PageTransition } from '@/components/ui/page-transition'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Settings, Bell, Palette, Database, Globe, Code, Save } from 'lucide-react'

export default function SettingsPage() {
  return (
    <PageTransition variant="fade">
      <div className="p-6 space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Settings</h1>
          <p className="text-muted-foreground mt-1">
            Configure your ElfAutomations.ai Control Center
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          {/* General Settings */}
          <Card variant="glass">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                General Settings
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Organization Name</label>
                  <input
                    type="text"
                    className="w-full mt-1 px-3 py-2 rounded-md bg-background border"
                    defaultValue="ElfAutomations"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Default Team Framework</label>
                  <select className="w-full mt-1 px-3 py-2 rounded-md bg-background border">
                    <option>CrewAI</option>
                    <option>LangGraph</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium">Default LLM Provider</label>
                  <select className="w-full mt-1 px-3 py-2 rounded-md bg-background border">
                    <option>OpenAI</option>
                    <option>Anthropic</option>
                  </select>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Notification Settings */}
          <Card variant="gradient">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="h-5 w-5" />
                Notifications
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <label className="flex items-center justify-between">
                  <span className="text-sm">Cost Alerts</span>
                  <input type="checkbox" defaultChecked className="toggle" />
                </label>
                <label className="flex items-center justify-between">
                  <span className="text-sm">Team Status Changes</span>
                  <input type="checkbox" defaultChecked className="toggle" />
                </label>
                <label className="flex items-center justify-between">
                  <span className="text-sm">Workflow Failures</span>
                  <input type="checkbox" defaultChecked className="toggle" />
                </label>
                <label className="flex items-center justify-between">
                  <span className="text-sm">Security Alerts</span>
                  <input type="checkbox" defaultChecked className="toggle" />
                </label>
                <label className="flex items-center justify-between">
                  <span className="text-sm">System Health Warnings</span>
                  <input type="checkbox" defaultChecked className="toggle" />
                </label>
              </div>
            </CardContent>
          </Card>

          {/* API Configuration */}
          <Card variant="neu">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Code className="h-5 w-5" />
                API Configuration
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium">API Base URL</label>
                  <input
                    type="text"
                    className="w-full mt-1 px-3 py-2 rounded-md bg-background border"
                    defaultValue="http://localhost:8001"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">WebSocket URL</label>
                  <input
                    type="text"
                    className="w-full mt-1 px-3 py-2 rounded-md bg-background border"
                    defaultValue="ws://localhost:8001/ws"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Polling Interval (seconds)</label>
                  <input
                    type="number"
                    className="w-full mt-1 px-3 py-2 rounded-md bg-background border"
                    defaultValue="30"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Theme Settings */}
          <Card variant="glass">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Palette className="h-5 w-5" />
                Appearance
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Theme</label>
                  <select className="w-full mt-1 px-3 py-2 rounded-md bg-background border">
                    <option>Dark (Default)</option>
                    <option>Light</option>
                    <option>System</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium">Primary Color</label>
                  <div className="flex gap-2 mt-1">
                    <div className="w-8 h-8 rounded bg-purple-500 cursor-pointer" />
                    <div className="w-8 h-8 rounded bg-blue-500 cursor-pointer" />
                    <div className="w-8 h-8 rounded bg-green-500 cursor-pointer" />
                    <div className="w-8 h-8 rounded bg-orange-500 cursor-pointer" />
                  </div>
                </div>
                <label className="flex items-center justify-between">
                  <span className="text-sm">Enable Animations</span>
                  <input type="checkbox" defaultChecked className="toggle" />
                </label>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Database Settings */}
        <Card variant="glass">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              Database Configuration
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="text-sm font-medium">Supabase URL</label>
                <input
                  type="text"
                  className="w-full mt-1 px-3 py-2 rounded-md bg-background border"
                  placeholder="https://your-project.supabase.co"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Supabase Anon Key</label>
                <input
                  type="password"
                  className="w-full mt-1 px-3 py-2 rounded-md bg-background border"
                  placeholder="••••••••"
                />
              </div>
            </div>
            <div className="mt-4">
              <Button variant="outline" size="sm">Test Connection</Button>
            </div>
          </CardContent>
        </Card>

        {/* Save Button */}
        <div className="flex justify-end gap-4">
          <Button variant="outline">Cancel</Button>
          <Button variant="gradient" className="gap-2">
            <Save className="h-4 w-4" />
            Save Settings
          </Button>
        </div>
      </div>
    </PageTransition>
  )
}
