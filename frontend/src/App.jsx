import { useState, useCallback } from 'react'
import InputSection from './components/InputSection'
import ConceptContainer from './components/ConceptContainer'
import GenerationModal from './components/GenerationModal'
import { usePipeline } from './hooks/usePipeline'

function App() {
  const {
    currentStep,
    concepts,
    characterization,
    isProcessing,
    extractConcepts,
    runCharacterization,
    startGeneration
  } = usePipeline()

  const [showGenerationModal, setShowGenerationModal] = useState(false)

  const handleTextSubmit = useCallback(async (text) => {
    await extractConcepts(text)
  }, [extractConcepts])

  const handleConceptsComplete = useCallback(async (selectedConcepts) => {
    await runCharacterization(selectedConcepts)
  }, [runCharacterization])

  const handleGenerationStart = useCallback((config) => {
    startGeneration(config)
    setShowGenerationModal(false)
  }, [startGeneration])

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">SD</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Synthetic Data Platform
                </h1>
                <p className="text-gray-600">
                  AI-powered combinatorial synthetic data generation
                </p>
              </div>
            </div>
            
            {/* Status indicator */}
            <div className="text-sm text-gray-600 flex items-center space-x-4">
              {concepts.length > 0 && (
                <div className="bg-primary-100 text-primary-800 px-3 py-1 rounded-full">
                  {concepts.length} concepts extracted
                </div>
              )}
              {Object.keys(characterization).length > 0 && (
                <div className="bg-green-100 text-green-800 px-3 py-1 rounded-full">
                  {Object.keys(characterization).length} dimensions characterized
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content - 2 columns */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Step 1-2: Input & Concept Extraction */}
            {currentStep <= 2 && (
              <InputSection
                onTextSubmit={handleTextSubmit}
                isProcessing={isProcessing}
                currentStep={currentStep}
              />
            )}

            {/* Step 2: Core Concepts Display */}
            {concepts.length > 0 && (
              <ConceptContainer
                title="Core Concepts"
                concepts={concepts.map(c => c.name)}
                layout="row"
                style="primary"
                loading={isProcessing && currentStep === 2}
                onComplete={handleConceptsComplete}
                showCompleteButton={currentStep === 2}
              />
            )}

            {/* Step 3: Multi-Dimensional Characterization */}
            {Object.keys(characterization).length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(characterization).map(([dimension, suggestions]) => (
                  <ConceptContainer
                    key={dimension}
                    title={`${dimension.charAt(0).toUpperCase() + dimension.slice(1)} Context`}
                    concepts={suggestions}
                    layout="column"
                    style="secondary"
                    loading={isProcessing && currentStep === 3}
                  />
                ))}
              </div>
            )}

          </div>

          {/* Sidebar - 1 column */}
          <div className="space-y-6">
            
            {/* Generation Controls */}
            {Object.keys(characterization).length > 0 && (
              <div className="bg-white rounded-lg shadow-sm p-6 border">
                <h3 className="text-lg font-semibold mb-4">
                  Generation Controls
                </h3>
                <button
                  onClick={() => setShowGenerationModal(true)}
                  disabled={isProcessing}
                  className="w-full bg-primary-600 text-white px-4 py-3 rounded-lg hover:bg-primary-700 transition-colors font-medium disabled:bg-gray-400"
                >
                  Start Generation
                </button>
                <div className="text-xs text-gray-500 mt-2">
                  Generate synthetic data in multiple formats
                </div>
              </div>
            )}

            {/* Instructions */}
            <div className="bg-gradient-to-br from-primary-50 to-green-50 rounded-lg p-6 border border-primary-200">
              <h3 className="text-lg font-semibold text-primary-900 mb-3">
                How it Works
              </h3>
              <div className="space-y-3 text-sm text-primary-800">
                <div className="flex items-start space-x-2">
                  <span className="font-bold text-primary-600">1.</span>
                  <span>Enter your text or upload a document</span>
                </div>
                <div className="flex items-start space-x-2">
                  <span className="font-bold text-primary-600">2.</span>
                  <span>AI extracts 20-50 core concepts</span>
                </div>
                <div className="flex items-start space-x-2">
                  <span className="font-bold text-primary-600">3.</span>
                  <span>5 specialized agents characterize concepts</span>
                </div>
                <div className="flex items-start space-x-2">
                  <span className="font-bold text-primary-600">4.</span>
                  <span>Review and customize selections</span>
                </div>
                <div className="flex items-start space-x-2">
                  <span className="font-bold text-primary-600">5.</span>
                  <span>Generate 50K+ synthetic data samples</span>
                </div>
              </div>
              
              {currentStep >= 3 && (
                <div className="mt-4 p-3 bg-primary-100 rounded-lg border border-primary-200">
                  <div className="text-sm text-primary-800 font-medium mb-1">
                    Ready for Generation
                  </div>
                  <div className="text-xs text-primary-700">
                    Multiple output formats available with quality validation
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

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