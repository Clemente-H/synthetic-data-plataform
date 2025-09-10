import { useState, useEffect } from 'react'
import { useWebSocket } from '../hooks/useWebSocket'

const WebSocketTest = () => {
  const [testText, setTestText] = useState("We are developing an AI-powered healthcare platform that helps doctors diagnose patients more efficiently.")
  const [taskId, setTaskId] = useState(null)
  const [progress, setProgress] = useState([])
  const [results, setResults] = useState(null)
  const [isExtracting, setIsExtracting] = useState(false)
  
  const {
    isConnected,
    connectionError,
    subscribeToTask,
    onPipelineProgress,
    onPipelineComplete,
    onPipelineError
  } = useWebSocket()

  // Set up WebSocket message handlers
  useEffect(() => {
    const cleanupProgress = onPipelineProgress((message) => {
      console.log('📈 Progress update:', message)
      setProgress(prev => [...prev, {
        type: 'progress',
        stage: message.stage,
        progress: message.progress,
        message: message.message,
        timestamp: message.timestamp
      }])
    })

    const cleanupComplete = onPipelineComplete((message) => {
      console.log('✅ Task complete:', message)
      setResults(message.results)
      setIsExtracting(false)
      setProgress(prev => [...prev, {
        type: 'complete',
        message: 'Task completed successfully',
        timestamp: message.timestamp
      }])
    })

    const cleanupError = onPipelineError((message) => {
      console.log('❌ Task error:', message)
      setIsExtracting(false)
      setProgress(prev => [...prev, {
        type: 'error',
        stage: message.stage,
        error: message.error,
        timestamp: message.timestamp
      }])
    })

    return () => {
      cleanupProgress()
      cleanupComplete()
      cleanupError()
    }
  }, [onPipelineProgress, onPipelineComplete, onPipelineError])

  const startExtraction = async () => {
    if (!isConnected) {
      alert('WebSocket not connected!')
      return
    }

    setIsExtracting(true)
    setProgress([])
    setResults(null)
    setTaskId(null)

    try {
      // Call the WebSocket extraction endpoint
      const response = await fetch('http://localhost:8000/api/extraction/extract-concepts-websocket', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          input_text: testText,
          max_concepts: 30,
          include_metadata: true
        })
      })

      const data = await response.json()
      
      if (data.status === 'started') {
        const newTaskId = data.task_id
        setTaskId(newTaskId)
        
        // Subscribe to WebSocket updates for this task
        subscribeToTask(newTaskId)
        
        setProgress([{
          type: 'info',
          message: `Task started with ID: ${newTaskId}`,
          timestamp: new Date().toISOString()
        }])
      } else {
        throw new Error('Failed to start extraction task')
      }
    } catch (error) {
      console.error('Failed to start extraction:', error)
      setIsExtracting(false)
      setProgress([{
        type: 'error',
        message: `Failed to start: ${error.message}`,
        timestamp: new Date().toISOString()
      }])
    }
  }

  const getProgressColor = (type) => {
    switch (type) {
      case 'progress': return 'text-blue-600'
      case 'complete': return 'text-green-600'
      case 'error': return 'text-red-600'
      default: return 'text-gray-600'
    }
  }

  const getProgressIcon = (type) => {
    switch (type) {
      case 'progress': return '📈'
      case 'complete': return '✅'
      case 'error': return '❌'
      default: return '📝'
    }
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold mb-4">WebSocket Integration Test</h2>
        
        {/* Connection Status */}
        <div className="mb-4 p-3 rounded-lg border-2">
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="font-medium">
              WebSocket: {isConnected ? 'Connected' : 'Disconnected'}
            </span>
            {connectionError && <span className="text-red-600">({connectionError})</span>}
          </div>
          {taskId && (
            <div className="mt-2 text-sm text-gray-600">
              Current Task: <span className="font-mono">{taskId}</span>
            </div>
          )}
        </div>

        {/* Test Input */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Test Input Text:
          </label>
          <textarea
            value={testText}
            onChange={(e) => setTestText(e.target.value)}
            className="w-full h-24 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            placeholder="Enter text to extract concepts from..."
            disabled={isExtracting}
          />
        </div>

        {/* Actions */}
        <div className="mb-6">
          <button
            onClick={startExtraction}
            disabled={!isConnected || isExtracting}
            className={`px-6 py-3 rounded-lg font-medium transition-all duration-200 ${
              !isConnected || isExtracting
                ? 'bg-gray-400 text-white cursor-not-allowed'
                : 'bg-primary-600 text-white hover:bg-primary-700 hover:shadow-md'
            }`}
          >
            {isExtracting ? 'Extracting...' : 'Start WebSocket Extraction'}
          </button>
        </div>
      </div>

      {/* Progress Log */}
      {progress.length > 0 && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-bold mb-4">Real-time Progress</h3>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {progress.map((item, index) => (
              <div key={index} className="p-3 rounded border-l-4 border-gray-200">
                <div className="flex items-start space-x-2">
                  <span className="text-lg">{getProgressIcon(item.type)}</span>
                  <div className="flex-1">
                    <div className={`font-medium ${getProgressColor(item.type)}`}>
                      {item.type === 'progress' && item.stage && `[${item.stage}] `}
                      {item.message || item.error}
                    </div>
                    {item.progress !== undefined && (
                      <div className="mt-1">
                        <div className="bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-primary-600 h-2 rounded-full transition-all duration-500"
                            style={{ width: `${Math.round(item.progress * 100)}%` }}
                          ></div>
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          {Math.round(item.progress * 100)}% complete
                        </div>
                      </div>
                    )}
                    <div className="text-xs text-gray-400 mt-1">
                      {new Date(item.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Results */}
      {results && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-bold mb-4">Extraction Results</h3>
          <div className="space-y-4">
            {results.concepts && (
              <div>
                <h4 className="font-medium text-gray-700 mb-2">
                  Concepts ({results.total_concepts_extracted}):
                </h4>
                <div className="flex flex-wrap gap-2">
                  {results.concepts.map((concept, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 bg-primary-100 text-primary-800 rounded-full text-sm font-medium"
                    >
                      {concept.name}
                    </span>
                  ))}
                </div>
              </div>
            )}
            
            <details className="mt-4">
              <summary className="cursor-pointer text-gray-600 hover:text-gray-800">
                View Raw Results
              </summary>
              <pre className="mt-2 p-3 bg-gray-100 rounded text-xs overflow-auto">
                {JSON.stringify(results, null, 2)}
              </pre>
            </details>
          </div>
        </div>
      )}
    </div>
  )
}

export default WebSocketTest