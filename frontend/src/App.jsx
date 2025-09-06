import { useState, useCallback, useEffect } from 'react'
import InputSection from './components/InputSection'
import ConceptContainer from './components/ConceptContainer'
import GenerationModal from './components/GenerationModal'
import StageIndicator from './components/StageIndicator'
import { usePipelineWebSocket } from './hooks/usePipelineWebSocket'

function App() {
  const {
    isConnected,
    currentStep,
    isProcessing,
    error,
    concepts,
    characterization,
    setCharacterization,
    generatedSamples,
    setGeneratedSamples,
    currentStage,
    overallProgress,
    inputText,
    setInputText,
    extractConcepts,
    runCharacterization,
    runFullPipeline,
    reset
  } = usePipelineWebSocket()

  const [showGenerationModal, setShowGenerationModal] = useState(false)
  const [selectedConcepts, setSelectedConcepts] = useState([])
  const [editableConcepts, setEditableConcepts] = useState([])
  const [newConceptText, setNewConceptText] = useState('')

  const handleTextSubmit = useCallback(async (text) => {
    await extractConcepts(text)
  }, [extractConcepts])

  const handleConceptsComplete = useCallback(async (selectedConcepts) => {
    setSelectedConcepts(selectedConcepts)
    await runCharacterization(selectedConcepts)
  }, [runCharacterization])

  // Sync concepts to editable concepts when they arrive
  useEffect(() => {
    if (concepts.length > 0 && editableConcepts.length === 0) {
      setEditableConcepts(concepts.map(c => typeof c === 'string' ? c : c.name))
    }
  }, [concepts, editableConcepts])

  // Auto-continue to characterization after concepts extraction (like HTML dummy)
  useEffect(() => {
    if (concepts.length > 0 && currentStep === 2 && !isProcessing) {
      // Auto-advance after 2 seconds to show concepts briefly
      const timer = setTimeout(() => {
        handleConceptsComplete(concepts)
      }, 2000)
      
      return () => clearTimeout(timer)
    }
  }, [concepts, currentStep, isProcessing, handleConceptsComplete])

  const handleAddConcepts = useCallback(() => {
    if (!newConceptText.trim()) return
    
    const newConcepts = newConceptText
      .split(',')
      .map(concept => concept.trim())
      .filter(concept => concept.length > 0)
      .filter(concept => !editableConcepts.includes(concept))
    
    setEditableConcepts(prev => [...prev, ...newConcepts])
    setNewConceptText('')
  }, [newConceptText, editableConcepts])

  const handleRemoveConcept = useCallback((conceptToRemove) => {
    setEditableConcepts(prev => prev.filter(c => c !== conceptToRemove))
  }, [])

  const handleRemoveDimensionContext = useCallback((dimension, contextToRemove) => {
    setCharacterization(prev => {
      const updated = { ...prev }
      if (updated[dimension]) {
        updated[dimension] = updated[dimension].filter(context => context !== contextToRemove)
      }
      return updated
    })
  }, [setCharacterization])

  const handleGenerationStart = useCallback(async (config) => {
    // Prepare the configuration for the backend
    const pipelineConfig = {
      input_text: inputText,
      format_type: config.format_type || 'qa',
      samples_per_combination: config.samples_per_combination || 3,
      max_total_samples: config.max_total_samples || 100,
      max_concepts: editableConcepts.length || concepts.length || 30
    }
    
    console.log('🚀 Starting generation with config:', pipelineConfig)
    
    try {
      await runFullPipeline(pipelineConfig)
      setShowGenerationModal(false)
    } catch (error) {
      console.error('❌ Generation failed:', error)
      // Keep modal open on error so user can retry
    }
  }, [runFullPipeline, inputText, editableConcepts, concepts])

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-6 py-6">
          <h1 className="text-3xl font-bold text-gray-900 text-center">
            Synthetic Data Generator
          </h1>
          <p className="text-gray-600 text-center mt-2">
            Generate high-quality training datasets through intelligent concept characterization
          </p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="space-y-8">
          {/* Input Section - Show until we have concepts */}
          {currentStep <= 2 && (
            <InputSection
              onTextSubmit={handleTextSubmit}
              isProcessing={isProcessing}
              currentStep={currentStep}
            />
          )}

          {/* Core Concepts Section - Show after extraction */}
          {concepts.length > 0 && currentStep >= 2 && (
            <div className={`bg-white rounded-2xl shadow-lg p-8 border slide-up ${isProcessing && currentStep === 2 ? 'breathing' : ''}`}>
              <div className="text-xl font-semibold text-gray-800 mb-6">
                Core Concepts Extracted
                {isProcessing && currentStep === 2 && (
                  <div className="inline-block ml-3">
                    <div className="loading-spinner"></div>
                  </div>
                )}
              </div>
              <div className="flex flex-wrap gap-3 mb-6">
                {editableConcepts.map((concept, index) => (
                  <div
                    key={index}
                    className="px-4 py-2 bg-green-100 text-green-800 rounded-full text-sm font-medium border border-green-200 group flex items-center"
                  >
                    {concept}
                    <button
                      onClick={() => handleRemoveConcept(concept)}
                      className="ml-2 text-green-600 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>

              
              {currentStep === 2 && !isProcessing && (
                <div className="text-center">
                  <button
                    onClick={() => handleConceptsComplete(concepts)}
                    className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium mr-4"
                  >
                    Continue Now
                  </button>
                  <div className="text-sm text-gray-500 mt-2">
                    Auto-advancing in 2 seconds...
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Dimensions Section - Show after characterization */}
          {Object.keys(characterization).length > 0 && currentStep >= 3 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
              {/* Geographic Contexts */}
              {characterization.geographic && (
                <div className={`bg-white rounded-2xl shadow-lg p-6 border slide-up ${isProcessing && currentStep === 3 ? 'breathing' : ''}`}>
                  <div className="text-lg font-semibold text-gray-800 mb-4">
                    Geographic Contexts
                    {isProcessing && currentStep === 3 && (
                      <div className="inline-block ml-2">
                        <div className="loading-spinner scale-75"></div>
                      </div>
                    )}
                  </div>
                  <div className="space-y-2">
                    {Array.isArray(characterization.geographic) ? characterization.geographic.map((context, index) => (
                      <div
                        key={index}
                        className="px-3 py-2 bg-blue-50 text-blue-700 rounded-lg text-sm border border-blue-200 hover:bg-blue-100 transition-colors group flex items-center justify-between"
                      >
                        <span>{context}</span>
                        <button
                          onClick={() => handleRemoveDimensionContext('geographic', context)}
                          className="text-blue-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          ×
                        </button>
                      </div>
                    )) : []}
                  </div>
                </div>
              )}

              {/* Linguistic Variations */}
              {characterization.linguistic && (
                <div className={`bg-white rounded-2xl shadow-lg p-6 border slide-up ${isProcessing && currentStep === 3 ? 'breathing' : ''}`}>
                  <div className="text-lg font-semibold text-gray-800 mb-4">
                    Linguistic Variations
                    {isProcessing && currentStep === 3 && (
                      <div className="inline-block ml-2">
                        <div className="loading-spinner scale-75"></div>
                      </div>
                    )}
                  </div>
                  <div className="space-y-2">
                    {Array.isArray(characterization.linguistic) ? characterization.linguistic.map((context, index) => (
                      <div
                        key={index}
                        className="px-3 py-2 bg-purple-50 text-purple-700 rounded-lg text-sm border border-purple-200 hover:bg-purple-100 transition-colors group flex items-center justify-between"
                      >
                        <span>{context}</span>
                        <button
                          onClick={() => handleRemoveDimensionContext('linguistic', context)}
                          className="text-purple-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          ×
                        </button>
                      </div>
                    )) : []}
                  </div>
                </div>
              )}

              {/* Cultural References */}
              {characterization.cultural && (
                <div className={`bg-white rounded-2xl shadow-lg p-6 border slide-up ${isProcessing && currentStep === 3 ? 'breathing' : ''}`}>
                  <div className="text-lg font-semibold text-gray-800 mb-4">
                    Cultural References
                    {isProcessing && currentStep === 3 && (
                      <div className="inline-block ml-2">
                        <div className="loading-spinner scale-75"></div>
                      </div>
                    )}
                  </div>
                  <div className="space-y-2">
                    {Array.isArray(characterization.cultural) ? characterization.cultural.map((context, index) => (
                      <div
                        key={index}
                        className="px-3 py-2 bg-orange-50 text-orange-700 rounded-lg text-sm border border-orange-200 hover:bg-orange-100 transition-colors group flex items-center justify-between"
                      >
                        <span>{context}</span>
                        <button
                          onClick={() => handleRemoveDimensionContext('cultural', context)}
                          className="text-orange-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          ×
                        </button>
                      </div>
                    )) : []}
                  </div>
                </div>
              )}

              {/* Persona Profiles */}
              {characterization.persona && (
                <div className={`bg-white rounded-2xl shadow-lg p-6 border slide-up ${isProcessing && currentStep === 3 ? 'breathing' : ''}`}>
                  <div className="text-lg font-semibold text-gray-800 mb-4">
                    Persona Profiles
                    {isProcessing && currentStep === 3 && (
                      <div className="inline-block ml-2">
                        <div className="loading-spinner scale-75"></div>
                      </div>
                    )}
                  </div>
                  <div className="space-y-2">
                    {Array.isArray(characterization.persona) ? characterization.persona.map((context, index) => (
                      <div
                        key={index}
                        className="px-3 py-2 bg-green-50 text-green-700 rounded-lg text-sm border border-green-200 hover:bg-green-100 transition-colors group flex items-center justify-between"
                      >
                        <span>{context}</span>
                        <button
                          onClick={() => handleRemoveDimensionContext('persona', context)}
                          className="text-green-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          ×
                        </button>
                      </div>
                    )) : []}
                  </div>
                </div>
              )}

              {/* Domain Specializations */}
              {characterization.domain && (
                <div className={`bg-white rounded-2xl shadow-lg p-6 border slide-up ${isProcessing && currentStep === 3 ? 'breathing' : ''}`}>
                  <div className="text-lg font-semibold text-gray-800 mb-4">
                    Domain Specializations
                    {isProcessing && currentStep === 3 && (
                      <div className="inline-block ml-2">
                        <div className="loading-spinner scale-75"></div>
                      </div>
                    )}
                  </div>
                  <div className="space-y-2">
                    {Array.isArray(characterization.domain) ? characterization.domain.map((context, index) => (
                      <div
                        key={index}
                        className="px-3 py-2 bg-indigo-50 text-indigo-700 rounded-lg text-sm border border-indigo-200 hover:bg-indigo-100 transition-colors group flex items-center justify-between"
                      >
                        <span>{context}</span>
                        <button
                          onClick={() => handleRemoveDimensionContext('domain', context)}
                          className="text-indigo-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          ×
                        </button>
                      </div>
                    )) : []}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Manual Concept Addition - Show after dimensions are loaded */}
          {Object.keys(characterization).length > 0 && currentStep >= 3 && !isProcessing && (
            <div className="bg-white rounded-2xl shadow-lg p-8 border slide-up">
              <div className="text-xl font-semibold text-gray-800 mb-6">
                Add More Concepts
              </div>
              <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                <div className="text-sm font-medium text-gray-700 mb-3">
                  Add additional concepts (comma-separated):
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={newConceptText}
                    onChange={(e) => setNewConceptText(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleAddConcepts()}
                    placeholder="concept1, concept2, concept3"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <button
                    onClick={handleAddConcepts}
                    disabled={!newConceptText.trim()}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-400"
                  >
                    Add
                  </button>
                </div>
              </div>

              {/* Show added concepts */}
              {editableConcepts.length > concepts.length && (
                <div className="mb-4">
                  <div className="text-sm font-medium text-gray-700 mb-2">
                    Added Concepts:
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {editableConcepts.slice(concepts.length).map((concept, index) => (
                      <div
                        key={index}
                        className="px-3 py-2 bg-blue-100 text-blue-800 rounded-lg text-sm border border-blue-200 group flex items-center"
                      >
                        {concept}
                        <button
                          onClick={() => handleRemoveConcept(concept)}
                          className="ml-2 text-blue-600 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Ready Button - Show only after all dimensions are loaded and no results yet */}
          {Object.keys(characterization).length > 0 && currentStep >= 3 && !isProcessing && generatedSamples.length === 0 && (
            <div className="text-center slide-up">
              <button
                onClick={() => setShowGenerationModal(true)}
                className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-8 py-4 rounded-xl hover:from-blue-700 hover:to-blue-800 transition-all font-semibold text-lg shadow-lg hover:shadow-xl transform hover:-translate-y-1"
              >
                Ready to Generate Dataset
              </button>
            </div>
          )}

          {/* Debug Info - Remove after fixing */}
          {isProcessing && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="text-sm text-yellow-800">
                <strong>Debug:</strong> Processing... Stage: {currentStage || 'unknown'} | Step: {currentStep} | Samples: {generatedSamples?.length || 0}
              </div>
              {currentStage === 'generation' && (
                <div className="text-xs text-yellow-600 mt-2">
                  Generation may take a while with large models. Please wait...
                </div>
              )}
            </div>
          )}

          {/* Results Section - Show after generation complete */}
          {generatedSamples && generatedSamples.length > 0 && (
            <div className="bg-white rounded-2xl shadow-lg p-8 border slide-up">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">
                    ✨ Generation Complete!
                  </h2>
                  <p className="text-gray-600 mt-1">
                    Successfully generated {generatedSamples.length} synthetic samples
                  </p>
                </div>
                <button
                  onClick={() => {
                    const dataStr = JSON.stringify(generatedSamples, null, 2)
                    const dataBlob = new Blob([dataStr], { type: 'application/json' })
                    const url = URL.createObjectURL(dataBlob)
                    const link = document.createElement('a')
                    link.href = url
                    link.download = `synthetic-dataset-${new Date().toISOString().slice(0, 10)}.json`
                    link.click()
                    URL.revokeObjectURL(url)
                  }}
                  className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition-colors font-medium flex items-center"
                >
                  📥 Download Dataset
                </button>
              </div>

              {/* Sample Preview */}
              <div className="bg-gray-50 rounded-lg p-4 mb-4">
                <h3 className="font-semibold text-gray-800 mb-3">Sample Preview:</h3>
                <div className="bg-white rounded border p-3 text-sm font-mono max-h-40 overflow-y-auto">
                  {generatedSamples[0] ? JSON.stringify(generatedSamples[0], null, 2) : 'No sample data available'}
                </div>
              </div>

              {/* Generation Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold text-green-700">{generatedSamples.length}</div>
                  <div className="text-sm text-green-600">Total Samples</div>
                </div>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold text-blue-700">{concepts.length}</div>
                  <div className="text-sm text-blue-600">Concepts Used</div>
                </div>
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold text-purple-700">{Object.keys(characterization).length}</div>
                  <div className="text-sm text-purple-600">Dimensions</div>
                </div>
                <div className="bg-orange-50 border border-orange-200 rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold text-orange-700">
                    {((generatedSamples.length > 0 ? JSON.stringify(generatedSamples).length : 0) / 1024).toFixed(1)}KB
                  </div>
                  <div className="text-sm text-orange-600">Dataset Size</div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center justify-center mt-6 space-x-4">
                <button
                  onClick={() => {
                    // Reset to generate again
                    setGeneratedSamples([])
                    setShowGenerationModal(true)
                  }}
                  className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  Generate More
                </button>
                <button
                  onClick={reset}
                  className="bg-gray-600 text-white px-6 py-3 rounded-lg hover:bg-gray-700 transition-colors font-medium"
                >
                  Start Over
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Stage Indicator - Bottom Right */}
      <StageIndicator
        currentStage={currentStage}
        overallProgress={overallProgress}
        isProcessing={isProcessing}
        isConnected={isConnected}
        error={error}
      />

      {/* Generation Modal */}
      {showGenerationModal && (
        <GenerationModal
          onClose={() => setShowGenerationModal(false)}
          onGenerate={handleGenerationStart}
          concepts={concepts}
          characterization={characterization}
        />
      )}
    </div>
  )
}

export default App