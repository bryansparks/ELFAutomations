'use client'

import { useState, useRef, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Bot, User, Send, Loader2, Sparkles, Copy, Check } from 'lucide-react'
import { api } from '@/services/api'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  suggestions?: string[]
}

interface WorkflowChatProps {
  onDescriptionUpdate?: (description: string) => void
  currentDescription?: string
}

export function WorkflowChat({ onDescriptionUpdate, currentDescription }: WorkflowChatProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: `Hi! I'm Claude, your AI workflow assistant. I can help you:

• Refine your workflow description
• Suggest improvements and edge cases
• Recommend best practices
• Help with specific n8n nodes and configurations

What kind of workflow would you like to create?`,
      timestamp: new Date(),
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
    }
  }, [messages])

  const handleSendMessage = async () => {
    if (!input.trim() || loading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      // Call API to get AI response
      const response = await api.chatWithWorkflowAssistant({
        messages: [...messages, userMessage].map(m => ({
          role: m.role,
          content: m.content
        })),
        currentDescription,
        context: 'workflow_creation'
      })

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.content,
        timestamp: new Date(),
        suggestions: response.suggestions,
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const handleCopyDescription = (content: string) => {
    navigator.clipboard.writeText(content)
    setCopiedId(content)
    setTimeout(() => setCopiedId(null), 2000)

    if (onDescriptionUpdate) {
      onDescriptionUpdate(content)
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion)
    inputRef.current?.focus()
  }

  const extractWorkflowDescriptions = (content: string): string[] => {
    // Extract text between quotes or after "workflow:" or "description:"
    const patterns = [
      /"([^"]+)"/g,
      /workflow:\s*(.+?)(?:\n|$)/gi,
      /description:\s*(.+?)(?:\n|$)/gi,
    ]

    const descriptions: string[] = []
    patterns.forEach(pattern => {
      const matches = content.matchAll(pattern)
      for (const match of matches) {
        const desc = match[1].trim()
        if (desc.length > 50 && desc.length < 500) {
          descriptions.push(desc)
        }
      }
    })

    return [...new Set(descriptions)]
  }

  return (
    <Card className="flex flex-col h-[60vh]">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Bot className="h-5 w-5" />
          AI Workflow Assistant
        </CardTitle>
        <CardDescription>
          Chat with Claude to refine your workflow ideas
        </CardDescription>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col">
        <ScrollArea className="flex-1 pr-4" ref={scrollAreaRef}>
          <div className="space-y-4">
            {messages.map((message) => {
              const isUser = message.role === 'user'
              const descriptions = !isUser ? extractWorkflowDescriptions(message.content) : []

              return (
                <div
                  key={message.id}
                  className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
                >
                  {!isUser && (
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                      <Bot className="h-4 w-4 text-primary" />
                    </div>
                  )}

                  <div className={`max-w-[80%] space-y-2`}>
                    <div
                      className={`rounded-lg px-4 py-2 ${
                        isUser
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted'
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    </div>

                    {/* Extracted workflow descriptions */}
                    {descriptions.length > 0 && (
                      <div className="space-y-2">
                        <p className="text-xs text-muted-foreground">Use these descriptions:</p>
                        {descriptions.map((desc, idx) => (
                          <Alert key={idx} className="cursor-pointer hover:bg-accent transition-colors">
                            <Sparkles className="h-4 w-4" />
                            <AlertDescription className="flex items-center justify-between">
                              <span className="text-sm mr-2">{desc}</span>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => handleCopyDescription(desc)}
                              >
                                {copiedId === desc ? (
                                  <Check className="h-3 w-3" />
                                ) : (
                                  <Copy className="h-3 w-3" />
                                )}
                              </Button>
                            </AlertDescription>
                          </Alert>
                        ))}
                      </div>
                    )}

                    {/* Suggestions */}
                    {message.suggestions && message.suggestions.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {message.suggestions.map((suggestion, idx) => (
                          <Button
                            key={idx}
                            size="sm"
                            variant="outline"
                            onClick={() => handleSuggestionClick(suggestion)}
                          >
                            {suggestion}
                          </Button>
                        ))}
                      </div>
                    )}

                    <p className="text-xs text-muted-foreground">
                      {message.timestamp.toLocaleTimeString()}
                    </p>
                  </div>

                  {isUser && (
                    <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center">
                      <User className="h-4 w-4" />
                    </div>
                  )}
                </div>
              )
            })}

            {loading && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                  <Bot className="h-4 w-4 text-primary" />
                </div>
                <div className="bg-muted rounded-lg px-4 py-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                </div>
              </div>
            )}
          </div>
        </ScrollArea>

        <div className="mt-4 flex gap-2">
          <Input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="Ask about workflows, nodes, or best practices..."
            disabled={loading}
          />
          <Button
            onClick={handleSendMessage}
            disabled={!input.trim() || loading}
            size="icon"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
