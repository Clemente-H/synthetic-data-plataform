import { useState } from 'react'

const GenerationModal = ({ onClose, onGenerate, concepts, characterization }) => {
  const [selectedFormat, setSelectedFormat] = useState('sft')
  const [samplesConfig, setSamplesConfig] = useState({
    geographic: 500,
    linguistic: 400,
    cultural: 600,
    persona: 450,
    domain: 550
  })
  const [isGenerating, setIsGenerating] = useState(false)

  const formatOptions = [
    { value: 'raw', label: 'Raw Data', description: 'Plain text examples' },
    { value: 'sft', label: 'SFT Format', description: 'Instruction-response pairs' },
    { value: 'dpo', label: 'DPO Format', description: 'Preference pairs' },
    { value: 'qa', label: 'Q&A Format', description: 'Question-answer pairs' }
  ]

  const updateEstimate = () => {
    const total = Object.values(samplesConfig).reduce((sum, val) => sum + val, 0)
    // Multiply by complexity levels and combinatorial factor
    return Math.floor(total * 5 * 10.2)
  }

  const handleUpdateSamples = (dimension, value) => {
    setSamplesConfig(prev => ({
      ...prev,
      [dimension]: parseInt(value) || 0
    }))
  }

  const handleGenerate = async () => {
    setIsGenerating(true)
    try {
      await onGenerate({
        format_type: selectedFormat,
        samples_per_combination: 3,
        max_total_samples: updateEstimate(),
        samples_config: samplesConfig
      })
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full mx-4 max-h-screen overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="p-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-2xl font-bold text-gray-900">
              Configure Generation
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-3xl font-light"
            >
              ×
            </button>
          </div>

          {/* Format Selection */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Select Output Format
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {formatOptions.map((format) => (
                <div
                  key={format.value}
                  onClick={() => setSelectedFormat(format.value)}
                  className={`p-4 rounded-xl border-2 cursor-pointer transition-all hover:shadow-md ${
                    selectedFormat === format.value 
                      ? 'border-blue-500 bg-blue-50' 
                      : 'border-gray-200 bg-white hover:border-gray-300'
                  }`}
                >
                  <div className="font-semibold text-gray-900 mb-1">{format.label}</div>
                  <div className="text-sm text-gray-600">{format.description}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Samples per Category */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Samples per Category
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {[
                { key: 'geographic', label: 'Geographic' },
                { key: 'linguistic', label: 'Linguistic' },
                { key: 'cultural', label: 'Cultural' },
                { key: 'persona', label: 'Personas' },
                { key: 'domain', label: 'Domain' }
              ].map(({ key, label }) => (
                <div key={key} className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    {label}
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="1000"
                    value={samplesConfig[key]}
                    onChange={(e) => handleUpdateSamples(key, e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-center font-medium"
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Estimated Dataset Size */}
          <div className="bg-gradient-to-r from-blue-50 to-green-50 rounded-xl p-6 mb-8 text-center">
            <div className="text-sm font-medium text-gray-600 mb-2">
              Estimated Total Dataset Size
            </div>
            <div className="text-4xl font-bold text-gray-900 mb-2">
              ~{updateEstimate().toLocaleString()}
            </div>
            <div className="text-sm text-gray-600">
              unique examples across 5 complexity levels
            </div>
          </div>

          {/* Generate Button */}
          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="w-full bg-gradient-to-r from-blue-600 to-blue-700 text-white px-8 py-4 rounded-xl hover:from-blue-700 hover:to-blue-800 transition-all font-semibold text-lg shadow-lg hover:shadow-xl transform hover:-translate-y-1 disabled:opacity-50 disabled:transform-none"
          >
            {isGenerating ? (
              <div className="flex items-center justify-center">
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-3"></div>
                {isGenerating === 'processing' ? 'Processing combinations...' : 
                 isGenerating === 'validation' ? 'Quality validation...' :
                 'Generating dataset...'}
              </div>
            ) : (
              'Generate Synthetic Dataset'
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

export default GenerationModal