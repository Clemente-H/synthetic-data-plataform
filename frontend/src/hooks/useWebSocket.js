import { useState, useEffect, useCallback, useRef } from 'react'

const WS_URL = 'ws://localhost:8000/api/ws'

export const useWebSocket = (clientId) => {
  const [isConnected, setIsConnected] = useState(false)
  const [connectionError, setConnectionError] = useState(null)
  const [messages, setMessages] = useState([])
  const [currentTask, setCurrentTask] = useState(null)
  
  const ws = useRef(null)
  const reconnectTimer = useRef(null)
  const messageHandlers = useRef({})

  // Generate client ID if not provided
  const finalClientId = clientId || `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

  const connect = useCallback(() => {
    try {
      ws.current = new WebSocket(`${WS_URL}/${finalClientId}`)
      
      ws.current.onopen = () => {
        console.log('🔌 WebSocket connected')
        setIsConnected(true)
        setConnectionError(null)
        
        // Clear reconnect timer if connection successful
        if (reconnectTimer.current) {
          clearTimeout(reconnectTimer.current)
          reconnectTimer.current = null
        }
      }
      
      ws.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          console.log('📨 WebSocket message received:', message)
          console.log('📨 Message type:', message.type)
          console.log('📨 Message task_id:', message.task_id)
          
          // Add to messages history
          setMessages(prev => [...prev.slice(-99), message]) // Keep last 100 messages
          
          // Call specific handlers
          const handler = messageHandlers.current[message.type]
          if (handler) {
            handler(message)
          }
          
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }
      
      ws.current.onclose = (event) => {
        console.log('🔌 WebSocket disconnected:', event.code, event.reason)
        setIsConnected(false)
        
        // Attempt to reconnect if not a deliberate close
        if (event.code !== 1000) {
          reconnectTimer.current = setTimeout(() => {
            console.log('🔄 Attempting to reconnect...')
            connect()
          }, 3000)
        }
      }
      
      ws.current.onerror = (error) => {
        console.error('🚨 WebSocket error:', error)
        setConnectionError('Connection failed')
        setIsConnected(false)
      }
      
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      setConnectionError('Failed to create connection')
    }
  }, [finalClientId])

  const disconnect = useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current)
      reconnectTimer.current = null
    }
    
    if (ws.current) {
      ws.current.close(1000) // Normal closure
      ws.current = null
    }
  }, [])

  const sendMessage = useCallback((message) => {
    if (ws.current && isConnected) {
      try {
        ws.current.send(JSON.stringify(message))
        return true
      } catch (error) {
        console.error('Failed to send WebSocket message:', error)
        return false
      }
    }
    return false
  }, [isConnected])

  const subscribeToTask = useCallback((taskId) => {
    const success = sendMessage({
      type: 'subscribe_task',
      task_id: taskId
    })
    
    if (success) {
      setCurrentTask(taskId)
      console.log(`📡 Subscribed to task: ${taskId}`)
    }
    
    return success
  }, [sendMessage])

  const ping = useCallback(() => {
    return sendMessage({
      type: 'ping',
      timestamp: new Date().toISOString()
    })
  }, [sendMessage])

  // Handler registration
  const onMessage = useCallback((messageType, handler) => {
    messageHandlers.current[messageType] = handler
    
    // Return cleanup function
    return () => {
      delete messageHandlers.current[messageType]
    }
  }, [])

  // Convenience handlers for common message types
  const onPipelineProgress = useCallback((handler) => {
    return onMessage('pipeline_progress', handler)
  }, [onMessage])

  const onPipelineError = useCallback((handler) => {
    return onMessage('pipeline_error', handler)
  }, [onMessage])

  const onPipelineComplete = useCallback((handler) => {
    return onMessage('pipeline_complete', handler)
  }, [onMessage])

  const onSampleGenerated = useCallback((handler) => {
    return onMessage('sample_generated', handler)
  }, [onMessage])

  // Auto-connect on mount with proper cleanup
  useEffect(() => {
    let mounted = true
    
    const connectIfMounted = () => {
      if (mounted) {
        connect()
      }
    }
    
    connectIfMounted()
    
    return () => {
      mounted = false
      disconnect()
    }
  }, []) // Remove dependencies to prevent reconnects

  // Health check ping every 30 seconds
  useEffect(() => {
    if (!isConnected) return
    
    const interval = setInterval(() => {
      ping()
    }, 30000)
    
    return () => clearInterval(interval)
  }, [isConnected, ping])

  return {
    // Connection state
    isConnected,
    connectionError,
    messages,
    currentTask,
    
    // Connection control
    connect,
    disconnect,
    
    // Messaging
    sendMessage,
    subscribeToTask,
    ping,
    
    // Event handlers
    onMessage,
    onPipelineProgress,
    onPipelineError,
    onPipelineComplete,
    onSampleGenerated,
    
    // Utilities
    clientId: finalClientId
  }
}