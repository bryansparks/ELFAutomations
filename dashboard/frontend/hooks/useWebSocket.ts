import { useEffect, useRef } from 'react'
import { io, Socket } from 'socket.io-client'
import { useDashboardStore } from '@/stores/dashboard'
import { useToast } from '@/components/ui/use-toast'

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'

export function useWebSocket() {
  const socketRef = useRef<Socket | null>(null)
  const { updateStats } = useDashboardStore()
  const { toast } = useToast()

  const connect = () => {
    if (socketRef.current?.connected) return

    // Create WebSocket connection
    const ws = new WebSocket(`${WS_URL}/ws`)

    ws.onopen = () => {
      console.log('WebSocket connected')
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        switch (data.type) {
          case 'stats_update':
            updateStats(data.data)
            break

          case 'alert':
            toast({
              title: data.title || 'Alert',
              description: data.message,
              variant: data.level === 'critical' ? 'destructive' : 'default',
            })
            break

          case 'team_update':
            // Refresh team data
            break

          case 'workflow_update':
            // Refresh workflow data
            break
        }
      } catch (error) {
        console.error('WebSocket message error:', error)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
      // Attempt to reconnect after 5 seconds
      setTimeout(() => {
        if (!socketRef.current?.connected) {
          connect()
        }
      }, 5000)
    }

    socketRef.current = ws as any
  }

  const disconnect = () => {
    if (socketRef.current) {
      socketRef.current.close()
      socketRef.current = null
    }
  }

  const sendMessage = (message: any) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(message))
    }
  }

  return {
    connect,
    disconnect,
    sendMessage,
  }
}
