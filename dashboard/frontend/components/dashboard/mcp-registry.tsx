'use client'

import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Puzzle, CheckCircle, XCircle, Tool } from 'lucide-react'

export function MCPRegistry() {
  const { data: mcps, isLoading } = useQuery({
    queryKey: ['mcps'],
    queryFn: api.getMCPs,
  })

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="h-32 bg-muted animate-pulse rounded" />
        ))}
      </div>
    )
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {mcps?.map((mcp: any, index: number) => (
        <Card key={index} className="p-4">
          <div className="flex items-start justify-between mb-2">
            <div className="flex items-center space-x-2">
              <Puzzle className="h-5 w-5 text-muted-foreground" />
              <h3 className="font-semibold">{mcp.name}</h3>
            </div>
            {mcp.status === 'active' ? (
              <CheckCircle className="h-4 w-4 text-green-500" />
            ) : (
              <XCircle className="h-4 w-4 text-red-500" />
            )}
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Type:</span>
              <Badge variant="outline">{mcp.type}</Badge>
            </div>

            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Tools:</span>
              <div className="flex items-center space-x-1">
                <Tool className="h-3 w-3" />
                <span className="font-medium">{mcp.tools}</span>
              </div>
            </div>

            {mcp.url && (
              <div className="text-xs text-muted-foreground truncate">
                {mcp.url}
              </div>
            )}
          </div>
        </Card>
      ))}
    </div>
  )
}

function Badge({ children, variant = "default", className = "" }: any) {
  const variants = {
    default: "bg-primary text-primary-foreground hover:bg-primary/80",
    secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
    outline: "text-foreground border border-input bg-background hover:bg-accent hover:text-accent-foreground",
    destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/80",
  }

  return (
    <div className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 ${variants[variant as keyof typeof variants]} ${className}`}>
      {children}
    </div>
  )
}
