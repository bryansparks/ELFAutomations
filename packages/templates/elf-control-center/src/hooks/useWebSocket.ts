import { useEffect, useRef, useState, useCallback } from 'react'

export enum ReadyState {
  CONNECTING = 0,
  OPEN = 1,
  CLOSING = 2,
  CLOSED = 3,
}

export interface Options {
  onOpen?: (event: Event) => void
  onClose?: (event: CloseEvent) => void
  onMessage?: (event: MessageEvent) => void
  onError?: (event: Event) => void
  shouldReconnect?: (closeEvent: CloseEvent) => boolean
  reconnectInterval?: number
  reconnectAttempts?: number
}

export interface SendMessage {
  (message: string): void
}

export function useWebSocket(
  url: string | null,
  options: Options = {}
): {
  sendMessage: SendMessage
  lastMessage: MessageEvent | null
  readyState: ReadyState
  getWebSocket: () => WebSocket | null
} {
  const [lastMessage, setLastMessage] = useState<MessageEvent | null>(null)
  const [readyState, setReadyState] = useState<ReadyState>(ReadyState.CLOSED)
  const webSocketRef = useRef<WebSocket | null>(null)
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttemptsRef = useRef(0)

  const {
    onOpen,
    onClose,
    onMessage,
    onError,
    shouldReconnect = () => true,
    reconnectInterval = 3000,
    reconnectAttempts = 10,
  } = options

  const connect = useCallback(() => {
    if (!url) return

    try {
      const ws = new WebSocket(url)
      webSocketRef.current = ws

      ws.onopen = (event) => {
        setReadyState(ReadyState.OPEN)
        reconnectAttemptsRef.current = 0
        onOpen?.(event)
      }

      ws.onclose = (event) => {
        setReadyState(ReadyState.CLOSED)
        onClose?.(event)

        if (shouldReconnect(event) && reconnectAttemptsRef.current < reconnectAttempts) {
          reconnectTimerRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++
            connect()
          }, reconnectInterval)
        }
      }

      ws.onmessage = (event) => {
        setLastMessage(event)
        onMessage?.(event)
      }

      ws.onerror = (event) => {
        onError?.(event)
      }

      setReadyState(ws.readyState)
    } catch (error) {
      console.error('WebSocket connection error:', error)
    }
  }, [url, onOpen, onClose, onMessage, onError, shouldReconnect, reconnectInterval, reconnectAttempts])

  const disconnect = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current)
      reconnectTimerRef.current = null
    }

    if (webSocketRef.current) {
      webSocketRef.current.close()
      webSocketRef.current = null
    }
  }, [])

  useEffect(() => {
    connect()
    return disconnect
  }, [connect, disconnect])

  const sendMessage = useCallback<SendMessage>((message) => {
    if (webSocketRef.current && webSocketRef.current.readyState === ReadyState.OPEN) {
      webSocketRef.current.send(message)
    } else {
      console.warn('WebSocket is not connected')
    }
  }, [])

  const getWebSocket = useCallback(() => webSocketRef.current, [])

  return {
    sendMessage,
    lastMessage,
    readyState,
    getWebSocket,
  }
}
