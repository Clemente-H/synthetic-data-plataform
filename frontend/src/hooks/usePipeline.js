import { useState, useCallback } from 'react'

const API_BASE = 'http://localhost:8000/api'

export const usePipeline = () => {
  const [currentStep, setCurrentStep] = useState(1)
  const [concepts, setConcepts] = useState([])
  const [characterization, setCharacterization] = useState({})
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState(null)

  const extractConcepts = useCallback(async (inputText) => {
    setIsProcessing(true)
    setError(null)
    setCurrentStep(2)

    try {
      const response = await fetch(`${API_BASE}/extraction/extract-concepts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          input_text: inputText,
          max_concepts: 30,
          include_metadata: true
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      
      if (data.status === 'success') {
        setConcepts(data.concepts)
        setCurrentStep(2)
      } else {
        throw new Error('Concept extraction failed')
      }
      
    } catch (err) {
      console.error('Concept extraction error:', err)
      setError(err.message)
    } finally {
      setIsProcessing(false)
    }
  }, [])

  const runCharacterization = useCallback(async (selectedConcepts) => {
    setIsProcessing(true)
    setError(null)
    setCurrentStep(3)

    try {
      const conceptNames = selectedConcepts.map(c => typeof c === 'string' ? c : c.name)
      
      const response = await fetch(`${API_BASE}/characterization/characterize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          core_concepts: conceptNames,
          agents_to_run: ['geographic', 'cultural', 'linguistic', 'persona', 'domain'],
          max_suggestions_per_agent: 12,
          run_parallel: false // Sequential to avoid overwhelming the system
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      
      if (data.status === 'success') {
        // Transform agent results to characterization format
        const characterizationData = {}
        Object.entries(data.agent_results).forEach(([agentType, result]) => {
          if (result.status === 'success') {
            characterizationData[agentType] = result.suggestions
          }
        })
        
        setCharacterization(characterizationData)
        setCurrentStep(4)
      } else {
        throw new Error('Characterization failed')
      }
      
    } catch (err) {
      console.error('Characterization error:', err)
      setError(err.message)
    } finally {
      setIsProcessing(false)
    }
  }, [])

  const startGeneration = useCallback(async (config) => {
    setIsProcessing(true)
    setError(null)
    setCurrentStep(5)

    try {
      const response = await fetch(`${API_BASE}/generation/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          concept_dimensions: characterization,
          format_type: config.format_type,
          samples_per_combination: config.samples_per_combination,
          complexity_levels: [1, 2, 3],
          max_total_samples: config.max_total_samples,
          include_metadata: true,
          quality_check: true
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      
      if (data.status === 'pending') {
        // Start polling for results
        pollGenerationStatus(data.task_id)
      } else {
        throw new Error('Generation failed to start')
      }
      
    } catch (err) {
      console.error('Generation error:', err)
      setError(err.message)
      setIsProcessing(false)
    }
  }, [characterization])

  const pollGenerationStatus = useCallback(async (taskId) => {
    const poll = async () => {
      try {
        const response = await fetch(`${API_BASE}/generation/status/${taskId}`)
        const data = await response.json()
        
        if (data.status === 'completed') {
          setCurrentStep(6)
          setIsProcessing(false)
          // You could fetch results here if needed
        } else if (data.status === 'failed') {
          setError(data.error_message || 'Generation failed')
          setIsProcessing(false)
        } else {
          // Still processing, poll again
          setTimeout(poll, 3000)
        }
      } catch (err) {
        console.error('Polling error:', err)
        setError('Status polling failed')
        setIsProcessing(false)
      }
    }
    
    poll()
  }, [])

  const reset = useCallback(() => {
    setCurrentStep(1)
    setConcepts([])
    setCharacterization({})
    setIsProcessing(false)
    setError(null)
  }, [])

  return {
    currentStep,
    concepts,
    characterization,
    isProcessing,
    error,
    extractConcepts,
    runCharacterization,
    startGeneration,
    reset
  }
}