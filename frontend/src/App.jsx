import { useState, useCallback, useEffect } from 'react'
import InputSection from './components/InputSection'
import ConceptContainer from './components/ConceptContainer'
import GenerationModal from './components/GenerationModal'
import ResultsModal from './components/ResultsModal'
import StageIndicator from './components/StageIndicator'
import DatasetSidebar from './components/DatasetSidebar'
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
    finalResults,
    currentStage,
    overallProgress,
    progressMessage,
    progressData,
    inputText,
    setInputText,
    extractConcepts,
    runCharacterization,
    runFullPipeline,
    reset
  } = usePipelineWebSocket()

  const [showGenerationModal, setShowGenerationModal] = useState(false)
  const [showResultsModal, setShowResultsModal] = useState(false)
  const [showDatasetSidebar, setShowDatasetSidebar] = useState(false)
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

  // Auto-open results modal when full pipeline completes (not just characterization)
  useEffect(() => {
    if (finalResults && (generatedSamples?.length > 0 || finalResults.final_data)) {
      setTimeout(() => setShowResultsModal(true), 1000) // Small delay to let user see completion
    }
  }, [finalResults, generatedSamples])

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-6 py-8">
          <h1 className="text-4xl font-bold text-gray-900 text-center">
            Synthetic Data Generator
          </h1>
          <p className="text-lg text-gray-600 text-center mt-3">
            Generate high-quality training datasets through intelligent concept characterization
          </p>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-6 py-10">
        <div className="space-y-10">
          {/* Input Section - Show until we have concepts */}
          {currentStep <= 2 && concepts.length === 0 && (
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
                    className="px-5 py-3 bg-gradient-to-r from-green-50 to-green-100 text-green-800 rounded-2xl text-sm font-semibold border-2 border-green-200 group flex items-center hover:from-green-100 hover:to-green-200 transition-all hover:shadow-md transform hover:-translate-y-1"
                  >
                    {concept}
                    <button
                      onClick={() => handleRemoveConcept(concept)}
                      className="ml-3 text-green-600 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all w-5 h-5 rounded-full hover:bg-red-100 flex items-center justify-center"
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
                        className="px-4 py-2 bg-gradient-to-r from-blue-50 to-blue-100 text-blue-700 rounded-xl text-sm border-2 border-blue-200 hover:from-blue-100 hover:to-blue-200 transition-all group flex items-center justify-between hover:shadow-sm"
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
                        className="px-4 py-2 bg-gradient-to-r from-purple-50 to-purple-100 text-purple-700 rounded-xl text-sm border-2 border-purple-200 hover:from-purple-100 hover:to-purple-200 transition-all group flex items-center justify-between hover:shadow-sm"
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
                        className="px-4 py-2 bg-gradient-to-r from-orange-50 to-orange-100 text-orange-700 rounded-xl text-sm border-2 border-orange-200 hover:from-orange-100 hover:to-orange-200 transition-all group flex items-center justify-between hover:shadow-sm"
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
                        className="px-4 py-2 bg-gradient-to-r from-green-50 to-green-100 text-green-700 rounded-xl text-sm border-2 border-green-200 hover:from-green-100 hover:to-green-200 transition-all group flex items-center justify-between hover:shadow-sm"
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
                        className="px-4 py-2 bg-gradient-to-r from-indigo-50 to-indigo-100 text-indigo-700 rounded-xl text-sm border-2 border-indigo-200 hover:from-indigo-100 hover:to-indigo-200 transition-all group flex items-center justify-between hover:shadow-sm"
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
              <div className="mb-6 p-6 bg-gradient-to-r from-gray-50 to-gray-100 rounded-2xl border border-gray-200">
                <div className="text-sm font-medium text-gray-700 mb-4">
                  Add additional concepts (comma-separated):
                </div>
                <div className="flex gap-3">
                  <input
                    type="text"
                    value={newConceptText}
                    onChange={(e) => setNewConceptText(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleAddConcepts()}
                    placeholder="concept1, concept2, concept3"
                    className="flex-1 px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all"
                  />
                  <button
                    onClick={handleAddConcepts}
                    disabled={!newConceptText.trim()}
                    className="px-6 py-3 bg-gradient-to-r from-green-600 to-green-700 text-white rounded-xl hover:from-green-700 hover:to-green-800 transition-all disabled:from-gray-400 disabled:to-gray-500 font-semibold shadow-lg hover:shadow-xl transform hover:-translate-y-1"
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
                  <div className="flex flex-wrap gap-3">
                    {editableConcepts.slice(concepts.length).map((concept, index) => (
                      <div
                        key={index}
                        className="px-4 py-2 bg-gradient-to-r from-blue-50 to-blue-100 text-blue-800 rounded-xl text-sm border-2 border-blue-200 group flex items-center hover:from-blue-100 hover:to-blue-200 transition-all hover:shadow-md transform hover:-translate-y-1"
                      >
                        {concept}
                        <button
                          onClick={() => handleRemoveConcept(concept)}
                          className="ml-3 text-blue-600 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all w-5 h-5 rounded-full hover:bg-red-100 flex items-center justify-center"
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
                className="bg-gradient-to-r from-green-600 to-green-700 text-white px-12 py-5 rounded-2xl hover:from-green-700 hover:to-green-800 transition-all font-bold text-xl shadow-xl hover:shadow-2xl transform hover:-translate-y-2 hover:scale-105"
              >
                Generate Dataset
              </button>
              <p className="text-gray-500 text-sm mt-3">
                Ready to create your synthetic dataset
              </p>
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

          {/* Results Notification - Show briefly before modal opens */}
          {finalResults && (generatedSamples?.length > 0 || finalResults.final_data) && !showResultsModal && (
            <div className="bg-gray-50 rounded-lg shadow-lg p-6 border border-gray-200 slide-up text-center">
              <div className="text-2xl font-bold text-gray-900 mb-2">
                Generation Complete
              </div>
              <div className="text-gray-600 mb-4">
                Results are ready! Opening details modal...
              </div>
              <button
                onClick={() => setShowResultsModal(true)}
                className="bg-gray-800 text-white px-6 py-3 rounded-lg hover:bg-gray-900 transition-colors font-medium"
              >
                View Results Now
              </button>
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
        progressMessage={progressMessage}
        progressData={progressData}
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

      {/* Results Modal */}
      <ResultsModal
        isOpen={showResultsModal}
        onClose={() => setShowResultsModal(false)}
        finalResults={finalResults}
        generatedSamples={generatedSamples}
        onOpenDatasets={() => {
          setShowResultsModal(false)
          setShowDatasetSidebar(true)
        }}
        onGenerateMore={() => {
          setShowResultsModal(false)
          setGeneratedSamples([])
          setShowGenerationModal(true)
        }}
        onReset={() => {
          setShowResultsModal(false)
          reset()
        }}
      />

      {/* Dataset Sidebar */}
      <DatasetSidebar
        isOpen={showDatasetSidebar}
        onClose={() => setShowDatasetSidebar(false)}
        finalResults={finalResults}
        generatedSamples={generatedSamples}
      />
    </div>
  )
}

export default App