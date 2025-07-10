'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  Send,
  X,
  Loader2,
  MessageCircle,
  CheckCircle,
  AlertCircle,
  Clock,
  Bot
} from 'lucide-react'
import { TeamInfo } from '@/services/api'
import { useWebSocket } from '@/hooks/useWebSocket'
import { cn } from '@/lib/utils'

interface TeamChatProps {
  team: TeamInfo
  onClose: () => void
  authToken?: string
}

interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  status?: 'sending' | 'sent' | 'error'
  metadata?: {
    thinking_time?: number
    tokens?: number
  }
}

interface DelegationPreview {
  title: string
  description: string
  estimated_hours?: number
  priority?: string
  target_teams?: string[]
}

export function TeamChat({ team, onClose, authToken }: TeamChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isConnected, setIsConnected] = useState(false)
  const [isThinking, setIsThinking] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [delegationPreview, setDelegationPreview] = useState<DelegationPreview | null>(null)
  const [error, setError] = useState<string | null>(null)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Construct WebSocket URL with JWT token
  const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}/teams/${team.name}/chat?token=${authToken}`

  const { sendMessage, lastMessage, readyState } = useWebSocket(wsUrl, {
    onOpen: () => {
      setIsConnected(true)
      setError(null)
    },
    onClose: () => {
      setIsConnected(false)
    },
    onError: (event) => {
      console.error('WebSocket error:', event)
      setError('Connection error. Please try again.')
      setIsConnected(false)
    },
    shouldReconnect: () => true,
    reconnectInterval: 3000,
  })

  // Handle incoming WebSocket messages
  useEffect(() => {
    if (!lastMessage) return

    try {
      const data = JSON.parse(lastMessage.data)

      switch (data.type) {
        case 'greeting':
          setSessionId(data.session_id)
          setMessages([{
            id: Date.now().toString(),
            role: 'assistant',
            content: data.message,
            timestamp: new Date(),
            status: 'sent'
          }])
          break

        case 'message':
          setIsThinking(false)
          setMessages(prev => [...prev, {
            id: Date.now().toString(),
            role: 'assistant',
            content: data.content,
            timestamp: new Date(),
            status: 'sent',
            metadata: {
              thinking_time: data.thinking_time,
              tokens: data.metadata?.total_tokens
            }
          }])

          if (data.ready_to_delegate) {
            // Show delegation readiness indicator
          }
          break

        case 'status':
          if (data.status === 'thinking') {
            setIsThinking(true)
          }
          break

        case 'delegation_preview':
          setDelegationPreview(data.delegation)
          break

        case 'session_ended':
          setIsConnected(false)
          break

        case 'error':
          setError(data.message || 'An error occurred')
          break
      }
    } catch (e) {
      console.error('Failed to parse WebSocket message:', e)
    }
  }, [lastMessage])

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSendMessage = useCallback(() => {
    if (!inputValue.trim() || !isConnected) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
      status: 'sending'
    }

    setMessages(prev => [...prev, userMessage])

    sendMessage(JSON.stringify({
      type: 'message',
      message: inputValue.trim(),
      session_id: sessionId
    }))

    setInputValue('')
    inputRef.current?.focus()

    // Update message status
    setTimeout(() => {
      setMessages(prev =>
        prev.map(msg =>
          msg.id === userMessage.id
            ? { ...msg, status: 'sent' }
            : msg
        )
      )
    }, 100)
  }, [inputValue, isConnected, sessionId, sendMessage])

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleConfirmDelegation = (confirmed: boolean) => {
    if (!sessionId || !delegationPreview) return

    // Send confirmation via API
    fetch(`/api/teams/${team.name}/chat/delegation/confirm`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify({
        session_id: sessionId,
        confirmed,
        modifications: null
      })
    })

    setDelegationPreview(null)
  }

  const getConnectionStatus = () => {
    if (error) return { text: 'Error', color: 'text-red-500' }
    if (!isConnected) return { text: 'Connecting...', color: 'text-yellow-500' }
    if (isThinking) return { text: 'Thinking...', color: 'text-blue-500' }
    return { text: 'Connected', color: 'text-green-500' }
  }

  const status = getConnectionStatus()

  return (
    <Card className="h-[600px] w-[500px] flex flex-col">
      <CardHeader className="flex flex-row items-center justify-between pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-primary/10">
            <MessageCircle className="h-5 w-5 text-primary" />
          </div>
          <div>
            <CardTitle className="text-lg">{team.display_name}</CardTitle>
            <p className="text-sm text-muted-foreground">
              Chat with {team.member_count > 0 ? 'team manager' : 'team'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className={cn("gap-1", status.color)}>
            {status.text === 'Thinking...' && <Loader2 className="h-3 w-3 animate-spin" />}
            {status.text === 'Connected' && <CheckCircle className="h-3 w-3" />}
            {status.text === 'Error' && <AlertCircle className="h-3 w-3" />}
            {status.text}
          </Badge>
          <Button size="icon" variant="ghost" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col p-0">
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={cn(
                  "flex gap-3",
                  message.role === 'user' ? "justify-end" : "justify-start"
                )}
              >
                {message.role === 'assistant' && (
                  <div className="p-2 rounded-full bg-primary/10 h-8 w-8 flex items-center justify-center">
                    <Bot className="h-4 w-4 text-primary" />
                  </div>
                )}
                <div
                  className={cn(
                    "rounded-lg px-4 py-2 max-w-[80%]",
                    message.role === 'user'
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted"
                  )}
                >
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  {message.metadata?.thinking_time && (
                    <p className="text-xs opacity-70 mt-1 flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {message.metadata.thinking_time.toFixed(1)}s
                    </p>
                  )}
                </div>
              </div>
            ))}
            {isThinking && (
              <div className="flex gap-3 justify-start">
                <div className="p-2 rounded-full bg-primary/10 h-8 w-8 flex items-center justify-center">
                  <Bot className="h-4 w-4 text-primary" />
                </div>
                <div className="rounded-lg px-4 py-2 bg-muted">
                  <div className="flex items-center gap-2">
                    <Loader2 className="h-3 w-3 animate-spin" />
                    <span className="text-sm">Thinking...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        {error && (
          <Alert variant="destructive" className="mx-4 mb-4">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {delegationPreview && (
          <div className="p-4 border-t">
            <div className="bg-muted rounded-lg p-4 space-y-3">
              <h4 className="font-semibold text-sm">Ready to delegate:</h4>
              <p className="text-sm">{delegationPreview.title}</p>
              <p className="text-xs text-muted-foreground">{delegationPreview.description}</p>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  onClick={() => handleConfirmDelegation(true)}
                >
                  Confirm & Delegate
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleConfirmDelegation(false)}
                >
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        )}

        <div className="p-4 border-t">
          <div className="flex gap-2">
            <Input
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message..."
              disabled={!isConnected || isThinking}
              className="flex-1"
            />
            <Button
              onClick={handleSendMessage}
              disabled={!isConnected || !inputValue.trim() || isThinking}
              size="icon"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
