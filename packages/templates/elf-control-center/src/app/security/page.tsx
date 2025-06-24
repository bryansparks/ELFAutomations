'use client'

import { PageTransition } from '@/components/ui/page-transition'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Shield, Lock, Key, AlertTriangle, CheckCircle, Users, FileWarning } from 'lucide-react'

export default function SecurityPage() {
  const securityMetrics = {
    credentials_encrypted: 42,
    credentials_total: 45,
    last_rotation: '5 days ago',
    access_violations: 0,
    active_sessions: 12,
  }

  const securityAlerts = [
    { id: '1', type: 'warning', message: '3 credentials need rotation', time: '2 hours ago' },
    { id: '2', type: 'info', message: 'Security audit completed successfully', time: '1 day ago' },
    { id: '3', type: 'success', message: 'All team credentials encrypted', time: '3 days ago' },
  ]

  return (
    <PageTransition variant="slide">
      <div className="p-6 space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Security Center</h1>
          <p className="text-muted-foreground mt-1">
            Manage credentials, access control, and security policies
          </p>
        </div>

        {/* Security Metrics */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card variant="glass">
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <Lock className="h-8 w-8 text-green-500" />
                <div>
                  <p className="text-2xl font-bold">{securityMetrics.credentials_encrypted}</p>
                  <p className="text-sm text-muted-foreground">Encrypted Credentials</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card variant="glass">
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <Key className="h-8 w-8 text-blue-500" />
                <div>
                  <p className="text-2xl font-bold">{securityMetrics.credentials_total}</p>
                  <p className="text-sm text-muted-foreground">Total Credentials</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card variant="glass">
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <AlertTriangle className="h-8 w-8 text-yellow-500" />
                <div>
                  <p className="text-2xl font-bold">{securityMetrics.access_violations}</p>
                  <p className="text-sm text-muted-foreground">Access Violations</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card variant="glass">
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <Users className="h-8 w-8 text-purple-500" />
                <div>
                  <p className="text-2xl font-bold">{securityMetrics.active_sessions}</p>
                  <p className="text-sm text-muted-foreground">Active Sessions</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          {/* Credential Management */}
          <Card variant="gradient">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Key className="h-5 w-5" />
                Credential Management
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center p-3 rounded-lg bg-background/50">
                  <span>OpenAI API Key</span>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <Button size="sm" variant="outline">Rotate</Button>
                  </div>
                </div>
                <div className="flex justify-between items-center p-3 rounded-lg bg-background/50">
                  <span>Anthropic API Key</span>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <Button size="sm" variant="outline">Rotate</Button>
                  </div>
                </div>
                <div className="flex justify-between items-center p-3 rounded-lg bg-background/50">
                  <span>Supabase Service Key</span>
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-yellow-500" />
                    <Button size="sm" variant="outline">Rotate</Button>
                  </div>
                </div>
                <div className="flex justify-between items-center p-3 rounded-lg bg-background/50">
                  <span>GitHub Token</span>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <Button size="sm" variant="outline">Rotate</Button>
                  </div>
                </div>
              </div>
              <div className="mt-4 pt-4 border-t">
                <p className="text-sm text-muted-foreground">
                  Last rotation: {securityMetrics.last_rotation}
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Security Alerts */}
          <Card variant="neu">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5" />
                Security Alerts
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {securityAlerts.map((alert) => (
                  <div key={alert.id} className="flex items-start gap-3 p-3 rounded-lg bg-muted/50">
                    {alert.type === 'warning' && <FileWarning className="h-5 w-5 text-yellow-500 mt-0.5" />}
                    {alert.type === 'info' && <Shield className="h-5 w-5 text-blue-500 mt-0.5" />}
                    {alert.type === 'success' && <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />}
                    <div className="flex-1">
                      <p className="text-sm">{alert.message}</p>
                      <p className="text-xs text-muted-foreground mt-1">{alert.time}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Access Control */}
        <Card variant="glass">
          <CardHeader>
            <CardTitle>Access Control Policy</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <h3 className="font-semibold mb-3">Team Access</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Engineering Team</span>
                    <span className="text-muted-foreground">Full MCP Access</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Marketing Team</span>
                    <span className="text-muted-foreground">Limited MCP Access</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Executive Team</span>
                    <span className="text-muted-foreground">Read-Only Access</span>
                  </div>
                </div>
              </div>
              <div>
                <h3 className="font-semibold mb-3">Security Features</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>Credential Encryption</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>Team-based Access Control</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>Audit Logging</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>Break-glass Access</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </PageTransition>
  )
}
