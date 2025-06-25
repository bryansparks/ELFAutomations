'use client'

import { useCallback, useEffect, useState } from 'react'
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  Position,
  Handle,
  NodeProps,
  MiniMap,
} from 'reactflow'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Webhook,
  Clock,
  Database,
  Mail,
  MessageSquare,
  Code,
  GitBranch,
  Globe,
  FileText,
  Cloud,
  AlertCircle,
} from 'lucide-react'
import 'reactflow/dist/style.css'

interface WorkflowVisualizerProps {
  workflow: any
  editable?: boolean
  onWorkflowChange?: (workflow: any) => void
}

// Node type to icon mapping
const nodeIcons: Record<string, any> = {
  'n8n-nodes-base.webhook': Webhook,
  'n8n-nodes-base.scheduleTrigger': Clock,
  'n8n-nodes-base.postgres': Database,
  'n8n-nodes-base.supabase': Database,
  'n8n-nodes-base.gmail': Mail,
  'n8n-nodes-base.emailSend': Mail,
  'n8n-nodes-base.slack': MessageSquare,
  'n8n-nodes-base.code': Code,
  'n8n-nodes-base.if': GitBranch,
  'n8n-nodes-base.switch': GitBranch,
  'n8n-nodes-base.httpRequest': Globe,
  'n8n-nodes-base.googleSheets': FileText,
  'n8n-nodes-base.googleDocs': FileText,
  'n8n-nodes-base.openAi': Cloud,
  'n8n-nodes-base.anthropic': Cloud,
  'n8n-nodes-langchain.toolMcp': Cloud,
}

// Node type to color mapping
const nodeColors: Record<string, string> = {
  webhook: '#22c55e',
  scheduleTrigger: '#3b82f6',
  database: '#8b5cf6',
  email: '#f59e0b',
  messaging: '#06b6d4',
  transform: '#6366f1',
  ai: '#ec4899',
  default: '#64748b',
}

// Custom node component
function CustomNode({ data }: NodeProps) {
  const Icon = nodeIcons[data.type] || AlertCircle

  // Determine node color based on type
  let color = nodeColors.default
  if (data.type.includes('webhook')) color = nodeColors.webhook
  else if (data.type.includes('schedule')) color = nodeColors.scheduleTrigger
  else if (data.type.includes('database') || data.type.includes('postgres') || data.type.includes('supabase')) color = nodeColors.database
  else if (data.type.includes('email') || data.type.includes('gmail')) color = nodeColors.email
  else if (data.type.includes('slack') || data.type.includes('message')) color = nodeColors.messaging
  else if (data.type.includes('code') || data.type.includes('if') || data.type.includes('switch')) color = nodeColors.transform
  else if (data.type.includes('openAi') || data.type.includes('anthropic') || data.type.includes('mcp')) color = nodeColors.ai

  return (
    <Card className="min-w-[200px] p-4 shadow-lg border-2" style={{ borderColor: color }}>
      <Handle type="target" position={Position.Left} className="w-3 h-3" style={{ background: color }} />

      <div className="flex items-center gap-2 mb-2">
        <div className="p-2 rounded-lg" style={{ backgroundColor: `${color}20` }}>
          <Icon className="h-5 w-5" style={{ color }} />
        </div>
        <div className="flex-1">
          <h3 className="font-semibold text-sm">{data.label}</h3>
          <p className="text-xs text-muted-foreground">{data.type.split('.').pop()}</p>
        </div>
      </div>

      {data.description && (
        <p className="text-xs text-muted-foreground mb-2">{data.description}</p>
      )}

      {data.parameters && Object.keys(data.parameters).length > 0 && (
        <div className="space-y-1">
          {Object.entries(data.parameters).slice(0, 3).map(([key, value]) => (
            <div key={key} className="flex justify-between text-xs">
              <span className="text-muted-foreground">{key}:</span>
              <span className="font-mono">{String(value).slice(0, 20)}</span>
            </div>
          ))}
          {Object.keys(data.parameters).length > 3 && (
            <p className="text-xs text-muted-foreground">+{Object.keys(data.parameters).length - 3} more</p>
          )}
        </div>
      )}

      <Handle type="source" position={Position.Right} className="w-3 h-3" style={{ background: color }} />
    </Card>
  )
}

const nodeTypes = {
  custom: CustomNode,
}

export function WorkflowVisualizer({ workflow, editable = false, onWorkflowChange }: WorkflowVisualizerProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])

  // Convert n8n workflow to React Flow format
  useEffect(() => {
    if (!workflow?.nodes) return

    // Convert nodes
    const flowNodes: Node[] = workflow.nodes.map((node: any, index: number) => ({
      id: node.id || node.name || `node-${index}`,
      type: 'custom',
      position: node.position ? { x: node.position[0], y: node.position[1] } : { x: 250 + index * 250, y: 100 + (index % 2) * 100 },
      data: {
        label: node.name,
        type: node.type,
        parameters: node.parameters || {},
        description: getNodeDescription(node),
      },
    }))

    // Convert connections to edges
    const flowEdges: Edge[] = []
    if (workflow.connections) {
      Object.entries(workflow.connections).forEach(([sourceId, connections]: [string, any]) => {
        if (connections.main) {
          connections.main.forEach((mainConnections: any[], outputIndex: number) => {
            mainConnections.forEach((connection: any) => {
              flowEdges.push({
                id: `${sourceId}-${connection.node}-${outputIndex}-${connection.index}`,
                source: sourceId,
                target: connection.node,
                sourceHandle: `output-${outputIndex}`,
                targetHandle: `input-${connection.index}`,
                animated: true,
                style: { stroke: '#64748b', strokeWidth: 2 },
              })
            })
          })
        }
      })
    }

    setNodes(flowNodes)
    setEdges(flowEdges)
  }, [workflow, setNodes, setEdges])

  // Get human-readable node description
  function getNodeDescription(node: any): string {
    const type = node.type?.split('.').pop() || ''

    switch (type) {
      case 'webhook':
        return `Webhook: ${node.parameters?.path || '/webhook'}`
      case 'scheduleTrigger':
        return `Schedule: ${getScheduleDescription(node.parameters?.rule)}`
      case 'postgres':
      case 'supabase':
        return `${node.parameters?.operation || 'query'} ${node.parameters?.table || 'table'}`
      case 'gmail':
        return node.parameters?.operation === 'send' ? 'Send email' : 'Read emails'
      case 'slack':
        return `Post to ${node.parameters?.channel || 'channel'}`
      case 'code':
        return 'Transform data'
      case 'if':
        return 'Conditional logic'
      case 'httpRequest':
        return `${node.parameters?.method || 'GET'} ${node.parameters?.url || 'URL'}`
      default:
        return ''
    }
  }

  function getScheduleDescription(rule: any): string {
    if (!rule) return 'Every interval'

    if (rule.cronExpression) {
      return `Cron: ${rule.cronExpression}`
    }

    if (rule.interval) {
      const interval = rule.interval[0]
      return `Every ${interval.intervalValue} ${interval.field}`
    }

    return 'Custom schedule'
  }

  const onConnect = useCallback((params: any) => {
    if (!editable) return
    // Handle connection creation in edit mode
  }, [editable])

  return (
    <div className="w-full h-[500px] bg-background rounded-lg border">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={editable ? onNodesChange : undefined}
        onEdgesChange={editable ? onEdgesChange : undefined}
        onConnect={editable ? onConnect : undefined}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        attributionPosition="bottom-right"
      >
        <Background variant="dots" gap={12} size={1} />
        <Controls />
        <MiniMap
          nodeColor={(node) => {
            const type = node.data?.type || ''
            if (type.includes('webhook')) return nodeColors.webhook
            if (type.includes('schedule')) return nodeColors.scheduleTrigger
            if (type.includes('database') || type.includes('postgres') || type.includes('supabase')) return nodeColors.database
            if (type.includes('email') || type.includes('gmail')) return nodeColors.email
            if (type.includes('slack')) return nodeColors.messaging
            if (type.includes('code') || type.includes('if')) return nodeColors.transform
            if (type.includes('openAi') || type.includes('anthropic')) return nodeColors.ai
            return nodeColors.default
          }}
          style={{
            backgroundColor: 'hsl(var(--background))',
            border: '1px solid hsl(var(--border))',
          }}
        />
      </ReactFlow>
    </div>
  )
}
