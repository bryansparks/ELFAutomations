'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Search,
  Filter,
  Star,
  Clock,
  Users,
  Cpu,
  Brain,
  Workflow,
  Download,
  Eye,
  Copy,
  CheckCircle,
  AlertCircle
} from 'lucide-react'
import { api } from '@/services/api'
import { WorkflowVisualizer } from './WorkflowVisualizer'

interface WorkflowTemplate {
  id: string
  name: string
  description: string
  category: string
  tags: string[]
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  estimatedTime: string
  nodeCount: number
  hasAI: boolean
  successRate: number
  usageCount: number
  workflow: any
  thumbnail?: string
}

interface TemplateGalleryProps {
  onSelectTemplate: (template: WorkflowTemplate) => void
  onDeployTemplate: (template: WorkflowTemplate) => void
}

export function TemplateGallery({ onSelectTemplate, onDeployTemplate }: TemplateGalleryProps) {
  const [templates, setTemplates] = useState<WorkflowTemplate[]>([])
  const [filteredTemplates, setFilteredTemplates] = useState<WorkflowTemplate[]>([])
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedTemplate, setSelectedTemplate] = useState<WorkflowTemplate | null>(null)
  const [previewOpen, setPreviewOpen] = useState(false)
  const [loading, setLoading] = useState(true)

  // Mock templates for demonstration
  const mockTemplates: WorkflowTemplate[] = [
    {
      id: '1',
      name: 'AI Customer Support Agent',
      description: 'Multi-channel support with AI agent, memory, and escalation',
      category: 'ai-powered',
      tags: ['ai', 'support', 'email', 'slack', 'memory'],
      difficulty: 'intermediate',
      estimatedTime: '30 mins',
      nodeCount: 12,
      hasAI: true,
      successRate: 94.5,
      usageCount: 1523,
      workflow: {
        nodes: [],
        connections: {}
      }
    },
    {
      id: '2',
      name: 'Document Analysis with RAG',
      description: 'Extract insights from documents using vector search and AI',
      category: 'ai-powered',
      tags: ['ai', 'rag', 'documents', 'analysis', 'vector'],
      difficulty: 'advanced',
      estimatedTime: '45 mins',
      nodeCount: 15,
      hasAI: true,
      successRate: 91.2,
      usageCount: 892,
      workflow: {
        nodes: [],
        connections: {}
      }
    },
    {
      id: '3',
      name: 'Multi-Agent Research Team',
      description: 'Coordinated AI agents for research and report generation',
      category: 'ai-powered',
      tags: ['ai', 'multi-agent', 'research', 'collaboration'],
      difficulty: 'advanced',
      estimatedTime: '60 mins',
      nodeCount: 20,
      hasAI: true,
      successRate: 88.7,
      usageCount: 456,
      workflow: {
        nodes: [],
        connections: {}
      }
    },
    {
      id: '4',
      name: 'ETL Data Pipeline',
      description: 'Extract, transform, and load data between systems',
      category: 'data-processing',
      tags: ['etl', 'data', 'database', 'transformation'],
      difficulty: 'intermediate',
      estimatedTime: '20 mins',
      nodeCount: 8,
      hasAI: false,
      successRate: 96.8,
      usageCount: 2341,
      workflow: {
        nodes: [],
        connections: {}
      }
    },
    {
      id: '5',
      name: 'Approval Workflow',
      description: 'Multi-level approval with notifications and escalation',
      category: 'business-process',
      tags: ['approval', 'notification', 'escalation', 'slack'],
      difficulty: 'beginner',
      estimatedTime: '15 mins',
      nodeCount: 10,
      hasAI: false,
      successRate: 98.2,
      usageCount: 3456,
      workflow: {
        nodes: [],
        connections: {}
      }
    },
    {
      id: '6',
      name: 'AI Content Generator',
      description: 'Generate and publish content with AI review process',
      category: 'ai-powered',
      tags: ['ai', 'content', 'generation', 'publishing', 'review'],
      difficulty: 'intermediate',
      estimatedTime: '25 mins',
      nodeCount: 11,
      hasAI: true,
      successRate: 92.4,
      usageCount: 1678,
      workflow: {
        nodes: [],
        connections: {}
      }
    }
  ]

  useEffect(() => {
    // In real implementation, fetch from API
    setTemplates(mockTemplates)
    setFilteredTemplates(mockTemplates)
    setLoading(false)
  }, [])

  useEffect(() => {
    // Filter templates based on category and search
    let filtered = templates

    if (selectedCategory !== 'all') {
      filtered = filtered.filter(t => t.category === selectedCategory)
    }

    if (searchQuery) {
      filtered = filtered.filter(t =>
        t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
      )
    }

    setFilteredTemplates(filtered)
  }, [selectedCategory, searchQuery, templates])

  const categories = [
    { id: 'all', name: 'All Templates', icon: Workflow },
    { id: 'ai-powered', name: 'AI-Powered', icon: Brain },
    { id: 'data-processing', name: 'Data Processing', icon: Cpu },
    { id: 'business-process', name: 'Business Process', icon: Users },
  ]

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return 'bg-green-500/20 text-green-500'
      case 'intermediate': return 'bg-yellow-500/20 text-yellow-500'
      case 'advanced': return 'bg-red-500/20 text-red-500'
      default: return 'bg-gray-500/20 text-gray-500'
    }
  }

  return (
    <div className="space-y-6">
      {/* Search and Filter Bar */}
      <div className="flex gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
          <input
            type="text"
            placeholder="Search templates..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-lg bg-background border"
          />
        </div>
        <Button variant="outline" size="icon">
          <Filter className="h-4 w-4" />
        </Button>
      </div>

      {/* Category Tabs */}
      <Tabs value={selectedCategory} onValueChange={setSelectedCategory}>
        <TabsList className="grid grid-cols-4 w-full">
          {categories.map(category => {
            const Icon = category.icon
            return (
              <TabsTrigger key={category.id} value={category.id} className="flex items-center gap-2">
                <Icon className="h-4 w-4" />
                <span className="hidden sm:inline">{category.name}</span>
              </TabsTrigger>
            )
          })}
        </TabsList>
      </Tabs>

      {/* Template Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {filteredTemplates.map(template => (
          <Card
            key={template.id}
            className="hover:shadow-lg transition-shadow cursor-pointer"
            onClick={() => {
              setSelectedTemplate(template)
              setPreviewOpen(true)
            }}
          >
            <CardHeader>
              <div className="flex justify-between items-start">
                <CardTitle className="text-lg">{template.name}</CardTitle>
                {template.hasAI && (
                  <Badge variant="secondary" className="ml-2">
                    <Brain className="h-3 w-3 mr-1" />
                    AI
                  </Badge>
                )}
              </div>
              <p className="text-sm text-muted-foreground mt-1">
                {template.description}
              </p>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {/* Tags */}
                <div className="flex flex-wrap gap-1">
                  {template.tags.slice(0, 3).map(tag => (
                    <Badge key={tag} variant="outline" className="text-xs">
                      {tag}
                    </Badge>
                  ))}
                  {template.tags.length > 3 && (
                    <Badge variant="outline" className="text-xs">
                      +{template.tags.length - 3}
                    </Badge>
                  )}
                </div>

                {/* Metrics */}
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="flex items-center gap-1">
                    <Clock className="h-3 w-3 text-muted-foreground" />
                    <span>{template.estimatedTime}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Workflow className="h-3 w-3 text-muted-foreground" />
                    <span>{template.nodeCount} nodes</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <CheckCircle className="h-3 w-3 text-green-500" />
                    <span>{template.successRate}%</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Users className="h-3 w-3 text-muted-foreground" />
                    <span>{template.usageCount} uses</span>
                  </div>
                </div>

                {/* Difficulty */}
                <div className="flex justify-between items-center">
                  <Badge className={getDifficultyColor(template.difficulty)}>
                    {template.difficulty}
                  </Badge>
                  <Button size="sm" variant="ghost">
                    <Eye className="h-4 w-4 mr-1" />
                    Preview
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Template Preview Dialog */}
      <Dialog open={previewOpen} onOpenChange={setPreviewOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {selectedTemplate?.name}
              {selectedTemplate?.hasAI && (
                <Badge variant="secondary">
                  <Brain className="h-3 w-3 mr-1" />
                  AI-Powered
                </Badge>
              )}
            </DialogTitle>
          </DialogHeader>

          {selectedTemplate && (
            <div className="space-y-4 overflow-y-auto max-h-[calc(90vh-200px)]">
              <p className="text-muted-foreground">
                {selectedTemplate.description}
              </p>

              {/* Template Details */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-3 rounded-lg bg-background">
                  <Clock className="h-5 w-5 mx-auto mb-1 text-muted-foreground" />
                  <p className="text-sm font-medium">{selectedTemplate.estimatedTime}</p>
                  <p className="text-xs text-muted-foreground">Setup Time</p>
                </div>
                <div className="text-center p-3 rounded-lg bg-background">
                  <Workflow className="h-5 w-5 mx-auto mb-1 text-muted-foreground" />
                  <p className="text-sm font-medium">{selectedTemplate.nodeCount} nodes</p>
                  <p className="text-xs text-muted-foreground">Workflow Size</p>
                </div>
                <div className="text-center p-3 rounded-lg bg-background">
                  <CheckCircle className="h-5 w-5 mx-auto mb-1 text-green-500" />
                  <p className="text-sm font-medium">{selectedTemplate.successRate}%</p>
                  <p className="text-xs text-muted-foreground">Success Rate</p>
                </div>
                <div className="text-center p-3 rounded-lg bg-background">
                  <Users className="h-5 w-5 mx-auto mb-1 text-muted-foreground" />
                  <p className="text-sm font-medium">{selectedTemplate.usageCount}</p>
                  <p className="text-xs text-muted-foreground">Times Used</p>
                </div>
              </div>

              {/* Tags */}
              <div>
                <h4 className="text-sm font-medium mb-2">Tags</h4>
                <div className="flex flex-wrap gap-2">
                  {selectedTemplate.tags.map(tag => (
                    <Badge key={tag} variant="outline">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Workflow Preview */}
              <div>
                <h4 className="text-sm font-medium mb-2">Workflow Structure</h4>
                <div className="h-[300px] border rounded-lg bg-background">
                  <WorkflowVisualizer workflow={selectedTemplate.workflow} />
                </div>
              </div>

              {/* Key Features */}
              <div>
                <h4 className="text-sm font-medium mb-2">Key Features</h4>
                <ul className="space-y-1">
                  <li className="flex items-center gap-2 text-sm">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    Pre-configured with best practices
                  </li>
                  <li className="flex items-center gap-2 text-sm">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    Error handling included
                  </li>
                  {selectedTemplate.hasAI && (
                    <li className="flex items-center gap-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      AI agents with safety controls
                    </li>
                  )}
                  <li className="flex items-center gap-2 text-sm">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    Ready to customize and deploy
                  </li>
                </ul>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                if (selectedTemplate) {
                  onSelectTemplate(selectedTemplate)
                  setPreviewOpen(false)
                }
              }}
            >
              <Copy className="h-4 w-4 mr-2" />
              Use as Template
            </Button>
            <Button
              onClick={() => {
                if (selectedTemplate) {
                  onDeployTemplate(selectedTemplate)
                  setPreviewOpen(false)
                }
              }}
            >
              <Download className="h-4 w-4 mr-2" />
              Deploy Now
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
