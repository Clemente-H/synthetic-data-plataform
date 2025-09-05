import { useState } from 'react'

const GenerationModal = ({ onClose, onGenerate, concepts, characterization }) => {
  const [config, setConfig] = useState({
    format_type: 'qa',
    samples_per_combination: 3,
    max_total_samples: 100
  })

  const formatOptions = [
    { value: 'qa', label: 'Q&A Pairs', description: 'Question-answer pairs for conversational training' },
    { value: 'sft', label: 'SFT Format', description: 'Instruction-response pairs for supervised fine-tuning' },
    { value: 'dpo', label: 'DPO Format', description: 'Preference pairs for direct preference optimization' },
    { value: 'raw', label: 'Raw Text', description: 'Unstructured text samples' }
  ]

  const estimatedCombinations = Object.values(characterization).reduce((acc, suggestions) => 
    acc * Math.min(suggestions.length, 12), 1
  )
  const estimatedSamples = Math.min(estimatedCombinations * config.samples_per_combination, config.max_total_samples)

  const handleGenerate = () => {
    onGenerate(config)
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-screen overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-900">
              Generation Configuration
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-xl"
            >
              ×
            </button>
          </div>

          {/* Format Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Output Format
            </label>
            <div className="space-y-2">
              {formatOptions.map((format) => (
                <label key={format.value} className="flex items-start space-x-3 cursor-pointer">
                  <input
                    type="radio"
                    name="format"
                    value={format.value}
                    checked={config.format_type === format.value}
                    onChange={(e) => setConfig(prev => ({ ...prev, format_type: e.target.value }))}
                    className="mt-1 h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
                  />
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">{format.label}</div>
                    <div className="text-sm text-gray-500">{format.description}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Sample Configuration */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Samples per Combination
              </label>
              <input
                type="number"
                min="1"
                max="20"
                value={config.samples_per_combination}
                onChange={(e) => setConfig(prev => ({ 
                  ...prev, 
                  samples_per_combination: parseInt(e.target.value) || 1 
                }))}
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Max Total Samples
              </label>
              <input
                type="number"
                min="10"
                max="10000"
                value={config.max_total_samples}
                onChange={(e) => setConfig(prev => ({ 
                  ...prev, 
                  max_total_samples: parseInt(e.target.value) || 100 
                }))}
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </div>

          {/* Generation Preview */}
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <h3 className="font-medium text-gray-900 mb-2">Generation Preview</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Concepts:</span>
                <span className="ml-2 font-medium">{concepts.length}</span>
              </div>
              <div>
                <span className="text-gray-500">Dimensions:</span>
                <span className="ml-2 font-medium">{Object.keys(characterization).length}</span>
              </div>
              <div>
                <span className="text-gray-500">Est. Combinations:</span>
                <span className="ml-2 font-medium">{estimatedCombinations.toLocaleString()}</span>
              </div>
              <div>
                <span className="text-gray-500">Est. Samples:</span>
                <span className="ml-2 font-medium text-primary-600">{estimatedSamples.toLocaleString()}</span>
              </div>
            </div>
          </div>

          {/* Characterization Summary */}
          <div className="mb-6">
            <h3 className="font-medium text-gray-900 mb-2">Characterization Summary</h3>
            <div className="space-y-2">
              {Object.entries(characterization).map(([dimension, suggestions]) => (
                <div key={dimension} className="flex items-center justify-between text-sm">
                  <span className="capitalize text-gray-600">{dimension}:</span>
                  <span className="text-gray-900">{suggestions.length} contexts</span>
                </div>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleGenerate}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
            >
              Start Generation
            </button>
          </div>

          {/* Processing Time Estimate */}
          <div className="mt-4 text-xs text-gray-500 text-center">
            Estimated processing time: {estimatedSamples < 100 ? '1-2 minutes' : estimatedSamples < 500 ? '5-10 minutes' : '10+ minutes'}
          </div>
        </div>
      </div>
    </div>
  )
}

export default GenerationModal