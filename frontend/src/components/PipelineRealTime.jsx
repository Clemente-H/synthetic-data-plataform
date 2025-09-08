import { useState, useEffect } from 'react'
import { usePipelineWebSocket } from '../hooks/usePipelineWebSocket'
import StageIndicator from './StageIndicator'

const PipelineRealTime = () => {
  const [inputText, setInputText] = useState(
    "We are developing an AI-powered healthcare platform that helps doctors diagnose patients more efficiently. The system uses machine learning algorithms to analyze medical images, patient history, and symptoms to provide accurate diagnoses and treatment recommendations."
  )
  const [pipelineConfig, setPipelineConfig] = useState({
    format_type: 'qa',
    samples_per_combination: 3,
    max_total_samples: 50,
    max_concepts: 30
  })
  const [datasets, setDatasets] = useState([])
  const [loadingDatasets, setLoadingDatasets] = useState(false)

  const {
    isConnected,
    currentStep,
    isProcessing,
    error,
    concepts,
    characterization, 
    generatedSamples,
    finalResults,
    progressLog,
    currentStage,
    overallProgress,
    progressMessage,
    progressData,
    runFullPipeline,
    extractConcepts,
    runCharacterization,
    reset
  } = usePipelineWebSocket()

  const handleFullPipeline = async () => {
    await runFullPipeline({
      input_text: inputText,
      ...pipelineConfig
    })
  }

  const handleConceptsOnly = async () => {
    await extractConcepts(inputText)
  }

  // Load available datasets
  const loadDatasets = async () => {
    setLoadingDatasets(true)
    try {
      const response = await fetch('http://localhost:8000/api/datasets/list')
      const data = await response.json()
      setDatasets(data.datasets || [])
    } catch (error) {
      console.error('Failed to load datasets:', error)
    } finally {
      setLoadingDatasets(false)
    }
  }

  // Download dataset
  const downloadDataset = (filename) => {
    const downloadUrl = `http://localhost:8000/api/datasets/download/${filename}`
    window.open(downloadUrl, '_blank')
  }

  // Load datasets on component mount and after pipeline completes
  useEffect(() => {
    loadDatasets()
  }, [])

  useEffect(() => {
    if (finalResults && !isProcessing) {
      // Refresh datasets list after pipeline completes
      setTimeout(loadDatasets, 1000)
    }
  }, [finalResults, isProcessing])

  const getStageColor = (stage) => {
    const colors = {
      'input_processing': 'bg-blue-100 text-blue-800',
      'concept_extraction': 'bg-green-100 text-green-800', 
      'characterization': 'bg-purple-100 text-purple-800',
      'agent_geographic': 'bg-yellow-100 text-yellow-800',
      'agent_cultural': 'bg-pink-100 text-pink-800',
      'agent_linguistic': 'bg-indigo-100 text-indigo-800',
      'agent_persona': 'bg-red-100 text-red-800',
      'agent_domain': 'bg-orange-100 text-orange-800',
      'human_validation': 'bg-teal-100 text-teal-800',
      'format_selection': 'bg-cyan-100 text-cyan-800',
      'generation': 'bg-emerald-100 text-emerald-800',
      'quality_assurance': 'bg-lime-100 text-lime-800',
      'export': 'bg-gray-100 text-gray-800'
    }
    return colors[stage] || 'bg-gray-100 text-gray-800'
  }

  const getProgressIcon = (type) => {
    const icons = {
      'progress': '📈',
      'complete': '✅',
      'error': '❌',
      'sample': '📝',
      'info': '📋'
    }
    return icons[type] || '📋'
  }

  const getPipelineStepName = (step) => {
    const steps = {
      1: 'Input Processing',
      2: 'Concept Extraction',
      3: 'Multi-Dimensional Characterization', 
      4: 'Human Validation',
      5: 'Format Selection',
      6: 'Combinatorial Generation',
      7: 'Quality Assurance',
      8: 'Export & Finalization'
    }
    return steps[step] || `Step ${step}`
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-900">🎭 Full Pipeline Real-Time</h2>
          <div className="flex items-center space-x-4">
            <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm ${
              isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
            }`}>
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
            </div>
            <button
              onClick={reset}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
            >
              Reset
            </button>
          </div>
        </div>

        {/* Overall Progress */}
        {isProcessing && (
          <div className="mb-4">
            <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
              <span>Overall Progress: {getPipelineStepName(currentStep)}</span>
              <span>{Math.round(overallProgress * 100)}%</span>
            </div>
            <div className="bg-gray-200 rounded-full h-3">
              <div 
                className="bg-gradient-to-r from-primary-500 to-primary-600 h-3 rounded-full transition-all duration-500"
                style={{ width: `${overallProgress * 100}%` }}
              ></div>
            </div>
            {currentStage && (
              <div className="mt-2">
                <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${getStageColor(currentStage)}`}>
                  {currentStage.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center space-x-2 text-red-800">
              <span className="text-lg">❌</span>
              <span className="font-medium">Pipeline Error</span>
            </div>
            <p className="text-red-700 mt-1">{error}</p>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Input & Config */}
        <div className="space-y-6">
          {/* Input Section */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-bold mb-4">📝 Input Text</h3>
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              className="w-full h-32 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none"
              placeholder="Enter your text to process through the pipeline..."
              disabled={isProcessing}
            />
            <div className="text-xs text-gray-500 mt-1">
              {inputText.length} characters
            </div>
          </div>

          {/* Pipeline Configuration */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-bold mb-4">⚙️ Configuration</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Output Format
                </label>
                <select
                  value={pipelineConfig.format_type}
                  onChange={(e) => setPipelineConfig(prev => ({ ...prev, format_type: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  disabled={isProcessing}
                >
                  <option value="qa">Q&A Pairs</option>
                  <option value="sft">SFT Format</option>
                  <option value="dpo">DPO Format</option>
                  <option value="raw">Raw Text</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Samples per Combo
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="20"
                    value={pipelineConfig.samples_per_combination}
                    onChange={(e) => setPipelineConfig(prev => ({ ...prev, samples_per_combination: parseInt(e.target.value) || 3 }))}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                    disabled={isProcessing}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Max Samples
                  </label>
                  <input
                    type="number"
                    min="10"
                    max="1000"
                    value={pipelineConfig.max_total_samples}
                    onChange={(e) => setPipelineConfig(prev => ({ ...prev, max_total_samples: parseInt(e.target.value) || 50 }))}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                    disabled={isProcessing}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Max Concepts
                </label>
                <input
                  type="number"
                  min="10"
                  max="50"
                  value={pipelineConfig.max_concepts}
                  onChange={(e) => setPipelineConfig(prev => ({ ...prev, max_concepts: parseInt(e.target.value) || 30 }))}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  disabled={isProcessing}
                />
              </div>
            </div>

            {/* Action Buttons */}
            <div className="mt-6 space-y-3">
              <button
                onClick={handleFullPipeline}
                disabled={!isConnected || isProcessing}
                className={`w-full py-3 px-4 rounded-lg font-medium transition-all duration-200 ${
                  !isConnected || isProcessing
                    ? 'bg-gray-400 text-white cursor-not-allowed'
                    : 'bg-primary-600 text-white hover:bg-primary-700 hover:shadow-md'
                }`}
              >
                {isProcessing ? '🎭 Running Full Pipeline...' : '🚀 Start Full Pipeline (8 Steps)'}
              </button>

              <button
                onClick={handleConceptsOnly}
                disabled={!isConnected || isProcessing}
                className={`w-full py-2 px-4 rounded-lg font-medium transition-all duration-200 ${
                  !isConnected || isProcessing
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                🧠 Extract Concepts Only
              </button>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-bold mb-4">📊 Live Stats</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Concepts:</span>
                <span className="font-medium">{concepts.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Dimensions:</span>
                <span className="font-medium">{Object.keys(characterization).length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Samples Generated:</span>
                <span className="font-medium text-primary-600">{generatedSamples.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Progress Events:</span>
                <span className="font-medium">{progressLog.length}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column - Real-time Progress & Results */}
        <div className="lg:col-span-2 space-y-6">
          {/* Real-time Progress Log */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-bold mb-4">📈 Real-time Progress</h3>
            <div className="max-h-96 overflow-y-auto space-y-2">
              {progressLog.length === 0 ? (
                <div className="text-center text-gray-500 py-8">
                  <div className="text-3xl mb-2">⏳</div>
                  <p>Start the pipeline to see real-time progress</p>
                </div>
              ) : (
                progressLog.map((entry, index) => (
                  <div key={index} className="p-3 border-l-4 border-gray-200 bg-gray-50 rounded">
                    <div className="flex items-start space-x-2">
                      <span className="text-lg">{getProgressIcon(entry.type)}</span>
                      <div className="flex-1">
                        <div className="font-medium text-gray-900">
                          {entry.message}
                        </div>
                        {entry.data && entry.data.estimated_duration && (
                          <div className="text-sm text-gray-600 mt-1">
                            Estimated: {entry.data.estimated_duration}
                          </div>
                        )}
                        {entry.progress !== undefined && (
                          <div className="mt-2">
                            <div className="bg-gray-200 rounded-full h-2">
                              <div 
                                className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                                style={{ width: `${Math.round(entry.progress * 100)}%` }}
                              ></div>
                            </div>
                            <div className="text-xs text-gray-500 mt-1">
                              {Math.round(entry.progress * 100)}% complete
                            </div>
                          </div>
                        )}
                        <div className="text-xs text-gray-400 mt-1">
                          {new Date(entry.timestamp).toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Extracted Concepts */}
          {concepts.length > 0 && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-bold mb-4">🧠 Extracted Concepts ({concepts.length})</h3>
              <div className="flex flex-wrap gap-2">
                {concepts.map((concept, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-primary-100 text-primary-800 rounded-full text-sm font-medium hover:-translate-y-0.5 transform transition-all duration-200"
                  >
                    {typeof concept === 'string' ? concept : concept.name}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Characterization Results */}
          {Object.keys(characterization).length > 0 && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-bold mb-4">🎯 Multi-Dimensional Characterization</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(characterization).map(([dimension, contexts]) => (
                  <div key={dimension} className="p-4 border border-gray-200 rounded-lg">
                    <h4 className="font-medium text-gray-800 mb-2 capitalize">
                      {dimension.replace(/_/g, ' ')} ({Array.isArray(contexts) ? contexts.length : 0})
                    </h4>
                    <div className="space-y-1">
                      {Array.isArray(contexts) && contexts.slice(0, 5).map((context, index) => (
                        <div key={index} className="text-sm text-gray-600 bg-gray-50 px-2 py-1 rounded">
                          {context}
                        </div>
                      ))}
                      {Array.isArray(contexts) && contexts.length > 5 && (
                        <div className="text-xs text-gray-500 italic">
                          +{contexts.length - 5} more contexts
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Generated Samples Preview */}
          {generatedSamples.length > 0 && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-bold mb-4">📝 Generated Samples ({generatedSamples.length})</h3>
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {generatedSamples.slice(0, 10).map((sample, index) => (
                  <div key={index} className="p-3 bg-gray-50 rounded-lg border">
                    <div className="text-sm">
                      <div className="font-medium text-gray-900 mb-1">Sample {index + 1}:</div>
                      <div className="text-gray-700 line-clamp-3">
                        {JSON.stringify(sample).substring(0, 200)}...
                      </div>
                    </div>
                  </div>
                ))}
                {generatedSamples.length > 10 && (
                  <div className="text-center text-sm text-gray-500 italic">
                    +{generatedSamples.length - 10} more samples...
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Final Results */}
          {finalResults && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-bold mb-4">🎉 Final Results</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div className="text-center p-3 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">
                    {finalResults.pipeline_metadata?.total_samples_generated || 0}
                  </div>
                  <div className="text-sm text-green-700">Samples</div>
                </div>
                <div className="text-center p-3 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">
                    {finalResults.pipeline_metadata?.concepts_extracted || 0}
                  </div>
                  <div className="text-sm text-blue-700">Concepts</div>
                </div>
                <div className="text-center p-3 bg-purple-50 rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">
                    {finalResults.pipeline_metadata?.files_exported || 0}
                  </div>
                  <div className="text-sm text-purple-700">Files</div>
                </div>
                <div className="text-center p-3 bg-orange-50 rounded-lg">
                  <div className="text-2xl font-bold text-orange-600">
                    {Math.round((finalResults.total_processing_time_seconds || 0) / 60)}m
                  </div>
                  <div className="text-sm text-orange-700">Duration</div>
                </div>
              </div>
              
              {/* Exported Files */}
              {finalResults.exported_files && finalResults.exported_files.length > 0 && (
                <div className="mb-4">
                  <h4 className="font-medium text-gray-800 mb-2">📁 Exported Files</h4>
                  <div className="space-y-2">
                    {finalResults.exported_files.map((file, index) => (
                      <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                        <div className="flex items-center space-x-2">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            file.format === 'json' ? 'bg-blue-100 text-blue-800' :
                            file.format === 'parquet' ? 'bg-green-100 text-green-800' :
                            file.format === 'csv' ? 'bg-orange-100 text-orange-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {file.format.toUpperCase()}
                          </span>
                          <span className="text-sm text-gray-700">{file.filename}</span>
                          <span className="text-xs text-gray-500">{file.size_mb} MB</span>
                        </div>
                        <button
                          onClick={() => downloadDataset(file.filename)}
                          className="px-2 py-1 bg-primary-600 text-white rounded hover:bg-primary-700 text-xs"
                        >
                          ⬇
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              <details>
                <summary className="cursor-pointer text-gray-600 hover:text-gray-800 font-medium">
                  View Complete Results
                </summary>
                <pre className="mt-3 p-4 bg-gray-100 rounded text-xs overflow-auto max-h-64">
                  {JSON.stringify(finalResults, null, 2)}
                </pre>
              </details>
            </div>
          )}

          {/* Available Datasets */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold">💾 Generated Datasets</h3>
              <button
                onClick={loadDatasets}
                disabled={loadingDatasets}
                className="px-3 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 text-sm disabled:opacity-50"
              >
                {loadingDatasets ? '🔄' : '↻'} Refresh
              </button>
            </div>

            {datasets.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                <div className="text-3xl mb-2">📁</div>
                <p>No datasets generated yet</p>
                <p className="text-sm mt-1">Run the pipeline to generate your first dataset</p>
              </div>
            ) : (
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {datasets.map((dataset, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border">
                    <div className="flex-1">
                      <div className="font-medium text-gray-900">
                        {dataset.format_type.toUpperCase()} Dataset
                      </div>
                      <div className="text-sm text-gray-600">
                        {dataset.file_format} • {dataset.size_mb} MB
                      </div>
                      <div className="text-xs text-gray-500">
                        {new Date(dataset.created_at).toLocaleString()}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        dataset.file_format === 'json' ? 'bg-blue-100 text-blue-800' :
                        dataset.file_format === 'parquet' ? 'bg-green-100 text-green-800' :
                        dataset.file_format === 'csv' ? 'bg-orange-100 text-orange-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {dataset.file_format}
                      </span>
                      <button
                        onClick={() => downloadDataset(dataset.filename)}
                        className="px-3 py-1 bg-primary-600 text-white rounded hover:bg-primary-700 text-sm"
                      >
                        ⬇ Download
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {datasets.length > 0 && (
              <div className="mt-4 text-xs text-gray-500 text-center">
                Total: {datasets.length} datasets • {datasets.reduce((sum, d) => sum + d.size_mb, 0).toFixed(2)} MB
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Floating Stage Indicator */}
      <StageIndicator 
        currentStage={currentStage}
        overallProgress={overallProgress}
        isProcessing={isProcessing}
        isConnected={isConnected}
        error={error}
        progressMessage={progressMessage}
        progressData={progressData}
      />
    </div>
  )
}

export default PipelineRealTime