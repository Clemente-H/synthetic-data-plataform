import { useState, useCallback, useEffect } from 'react'
import { useWebSocket } from './useWebSocket'

const API_BASE = 'http://localhost:8000/api'

export const usePipelineWebSocket = () => {
  // Pipeline state
  const [currentStep, setCurrentStep] = useState(1)
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState(null)
  const [currentTask, setCurrentTask] = useState(null)
  const [inputText, setInputText] = useState('')
  
  // Pipeline data
  const [concepts, setConcepts] = useState([])
  const [selectedConcepts, setSelectedConcepts] = useState([])
  const [characterization, setCharacterization] = useState({})
  const [generatedSamples, setGeneratedSamples] = useState([])
  const [finalResults, setFinalResults] = useState(null)
  
  // Real-time progress
  const [progressLog, setProgressLog] = useState([])
  const [currentStage, setCurrentStage] = useState(null)
  const [overallProgress, setOverallProgress] = useState(0)
  const [progressMessage, setProgressMessage] = useState('')
  const [progressData, setProgressData] = useState(null)
  
  // WebSocket integration
  const {
    isConnected,
    subscribeToTask,
    onPipelineProgress,
    onPipelineComplete, 
    onPipelineError,
    onSampleGenerated
  } = useWebSocket()

  // Auto-continue characterization after concepts are extracted (temporarily disabled)
  // useEffect(() => {
  //   if (selectedConcepts.length > 0 && concepts.length > 0 && currentStep === 2 && !isProcessing) {
  //     setTimeout(() => {
  //       runCharacterization(selectedConcepts)
  //     }, 1500) // Show concepts for 1.5 seconds then continue
  //   }
  // }, [selectedConcepts, concepts, currentStep, isProcessing])

  // Setup WebSocket listeners
  const setupWebSocketListeners = useCallback((taskId) => {
    console.log(`📡 Setting up WebSocket listeners for task: ${taskId}`)
    
    // Subscribe to task updates
    subscribeToTask(taskId)
    
    // Progress updates
    const cleanupProgress = onPipelineProgress((message) => {
      console.log('📈 Pipeline progress:', message)
      
      setProgressLog(prev => [...prev, {
        type: 'progress',
        stage: message.stage,
        progress: message.progress,
        message: message.message,
        data: message.data,
        timestamp: message.timestamp
      }])
      
      setCurrentStage(message.stage)
      setOverallProgress(message.progress || 0)
      setProgressMessage(message.message || '')
      setProgressData(message.data || null)
      
      // Update pipeline step based on stage
      const stageToStep = {
        'input_processing': 1,
        'concept_extraction': 2, 
        'characterization': 3,
        'human_validation': 4,
        'format_selection': 5,
        'generation': 6,
        'quality_assurance': 7,
        'export': 8
      }
      
      const step = stageToStep[message.stage] || currentStep
      setCurrentStep(step)
      
      // Update concepts if available
      if (message.data?.concepts) {
        setConcepts(message.data.concepts)
      }
      
      // Update characterization if available
      if (message.data?.characterization) {
        setCharacterization(message.data.characterization)
      }
    })
    
    // Completion handler
    const cleanupComplete = onPipelineComplete((message) => {
      console.log('✅ Pipeline complete received:', message)
      console.log('✅ Final results data:', message.results)
      
      setProgressLog(prev => [...prev, {
        type: 'complete',
        message: '🎉 Pipeline completed successfully!',
        timestamp: message.timestamp
      }])
      
      setIsProcessing(false)
      setCurrentStep(8)
      setOverallProgress(1.0)
      setFinalResults(message.results)
      console.log('🔥 setFinalResults called with:', message.results)
      console.log('🔥 Should trigger re-render now!')
      
      // Extract concepts from extraction completion
      if (message.results?.concepts) {
        setConcepts(message.results.concepts)
        setCurrentStep(2) // Set to concepts display step
        
        // Auto-continue with characterization (temporarily disabled)
      }
      
      // Extract characterization from characterization completion
      if (message.results?.characterization) {
        setCharacterization(message.results.characterization)
        setCurrentStep(3) // Set to characterization display step
      }
      
      // Extract final data from full pipeline results
      if (message.results?.final_data?.samples) {
        setGeneratedSamples(message.results.final_data.samples)
      }
      
      if (message.results?.pipeline_metadata?.concepts_extracted) {
        // Update with final concept count - already handled above
      }
    })
    
    // Error handler
    const cleanupError = onPipelineError((message) => {
      console.log('❌ Pipeline error:', message)
      
      setProgressLog(prev => [...prev, {
        type: 'error',
        stage: message.stage,
        error: message.error,
        timestamp: message.timestamp
      }])
      
      setError(message.error)
      setIsProcessing(false)
    })
    
    // Sample streaming handler
    const cleanupSamples = onSampleGenerated((message) => {
      console.log('📝 Sample generated:', message)
      
      setGeneratedSamples(prev => [...prev, message.sample])
      
      setProgressLog(prev => [...prev, {
        type: 'sample',
        message: `Sample ${message.progress.generated}/${message.progress.expected} generated (${message.progress.percentage.toFixed(1)}%)`,
        data: message.sample,
        timestamp: message.timestamp
      }])
    })
    
    return () => {
      cleanupProgress()
      cleanupComplete()
      cleanupError()
      cleanupSamples()
    }
  }, [subscribeToTask, onPipelineProgress, onPipelineComplete, onPipelineError, onSampleGenerated, currentStep])

  // Full pipeline execution
  const runFullPipeline = useCallback(async (config) => {
    if (!isConnected) {
      setError('WebSocket not connected')
      return false
    }
    
    setIsProcessing(true)
    setError(null)
    setProgressLog([])
    setConcepts([])
    setCharacterization({})
    setGeneratedSamples([])
    setFinalResults(null)
    setCurrentStep(1)
    setOverallProgress(0)
    
    try {
      console.log('🚀 Starting full pipeline with config:', config)
      
      const response = await fetch(`${API_BASE}/pipeline/run-full-pipeline`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          input_text: config.input_text,
          format_type: config.format_type || 'qa',
          samples_per_combination: config.samples_per_combination || 3,
          max_total_samples: config.max_total_samples || 100,
          max_concepts: config.max_concepts || 30
        })
      })
      
      const data = await response.json()
      
      if (data.status === 'started') {
        const taskId = data.task_id
        setCurrentTask(taskId)
        
        setProgressLog([{
          type: 'info',
          message: `🚀 Full pipeline started - Task ID: ${taskId}`,
          data: { estimated_duration: data.estimated_duration },
          timestamp: new Date().toISOString()
        }])
        
        // Setup WebSocket listeners for this task
        const cleanup = setupWebSocketListeners(taskId)
        
        // Store cleanup function for later use
        setCurrentTask(prev => ({ ...prev, cleanup }))
        
        return true
      } else {
        throw new Error(data.message || 'Failed to start pipeline')
      }
      
    } catch (err) {
      console.error('Failed to start pipeline:', err)
      setError(err.message)
      setIsProcessing(false)
      return false
    }
  }, [isConnected, setupWebSocketListeners])
  
  // Concept extraction only
  const extractConcepts = useCallback(async (text) => {
    setInputText(text) // Store the input text
    if (!isConnected) {
      setError('WebSocket not connected')
      return false
    }
    
    setIsProcessing(true)
    setError(null)
    setProgressLog([])
    setCurrentStep(2)
    
    try {
      const response = await fetch(`${API_BASE}/extraction/extract-concepts-websocket`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          input_text: text,
          max_concepts: 30,
          include_metadata: true
        })
      })
      
      const data = await response.json()
      
      if (data.status === 'started') {
        const taskId = data.task_id
        setCurrentTask(taskId)
        
        const cleanup = setupWebSocketListeners(taskId)
        setCurrentTask(prev => ({ ...prev, cleanup }))
        
        return true
      }
      
    } catch (err) {
      setError(err.message)
      setIsProcessing(false)
    }
  }, [isConnected, setupWebSocketListeners])
  
  // Characterization with individual agent progress
  const runCharacterization = useCallback(async (conceptList) => {
    if (!isConnected) {
      setError('WebSocket not connected')
      return false
    }
    
    setIsProcessing(true)
    setError(null)
    setCurrentStep(3)
    
    try {
      const response = await fetch(`${API_BASE}/pipeline/characterize-websocket`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          concepts: conceptList.map(c => typeof c === 'string' ? c : c.name),
          agents_to_run: ['geographic', 'cultural', 'linguistic', 'persona', 'domain']
        })
      })
      
      const data = await response.json()
      
      if (data.status === 'started') {
        const taskId = data.task_id
        setCurrentTask(taskId)
        
        const cleanup = setupWebSocketListeners(taskId)
        setCurrentTask(prev => ({ ...prev, cleanup }))
        
        return true
      }
      
    } catch (err) {
      setError(err.message)
      setIsProcessing(false)
    }
  }, [isConnected, setupWebSocketListeners])
  
  // Reset pipeline state
  const reset = useCallback(() => {
    setCurrentStep(1)
    setIsProcessing(false)
    setError(null)
    setCurrentTask(null)
    setConcepts([])
    setCharacterization({})
    setGeneratedSamples([])
    setFinalResults(null)
    setProgressLog([])
    setCurrentStage(null)
    setOverallProgress(0)
  }, [])

  return {
    // Connection state
    isConnected,
    
    // Pipeline state
    currentStep,
    isProcessing,
    error,
    currentTask,
    inputText,
    setInputText,
    
    // Pipeline data
    concepts,
    characterization,
    setCharacterization,
    generatedSamples,
    setGeneratedSamples,
    finalResults,
    
    // Real-time progress
    progressLog,
    currentStage,
    overallProgress,
    progressMessage,
    progressData,
    
    // Pipeline actions
    runFullPipeline,
    extractConcepts,
    runCharacterization,
    reset
  }
}