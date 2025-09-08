import { useState } from 'react'

const ResultsModal = ({ isOpen, onClose, finalResults, generatedSamples, onOpenDatasets, onGenerateMore, onReset }) => {
  const [selectedExport, setSelectedExport] = useState('json')
  
  if (!isOpen || !finalResults) return null

  const exportFormats = [
    { value: 'json', label: 'JSON', description: 'Raw data format' },
    { value: 'csv', label: 'CSV', description: 'Spreadsheet compatible' },
    { value: 'parquet', label: 'Parquet', description: 'Columnar format' },
    { value: 'huggingface', label: 'HF Dataset', description: 'HuggingFace ready' }
  ]

  // Download current results
  const downloadCurrentResults = (format = 'json') => {
    if (!generatedSamples || generatedSamples.length === 0) return
    
    let dataStr, filename, mimeType
    
    switch (format) {
      case 'csv':
        // Convert to CSV
        if (generatedSamples.length > 0) {
          const headers = Object.keys(generatedSamples[0])
          const csvRows = [
            headers.join(','),
            ...generatedSamples.map(row => 
              headers.map(header => {
                const value = row[header]
                // Escape quotes and wrap in quotes if contains comma
                return typeof value === 'string' && value.includes(',') 
                  ? `"${value.replace(/"/g, '""')}"` 
                  : value
              }).join(',')
            )
          ]
          dataStr = csvRows.join('\n')
          mimeType = 'text/csv'
          filename = `synthetic-dataset-${new Date().toISOString().slice(0, 10)}.csv`
        }
        break
      default:
        dataStr = JSON.stringify(generatedSamples, null, 2)
        mimeType = 'application/json'
        filename = `synthetic-dataset-${new Date().toISOString().slice(0, 10)}.json`
    }
    
    const dataBlob = new Blob([dataStr], { type: mimeType })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    link.click()
    URL.revokeObjectURL(url)
  }

  const formatFileSize = (size) => {
    if (!size) return 'Unknown'
    if (size < 1024) return size + ' B'
    if (size < 1024 * 1024) return Math.round(size / 1024) + ' KB'
    return Math.round(size / (1024 * 1024)) + ' MB'
  }

  const samplesCount = generatedSamples?.length || finalResults?.final_data?.total_samples || 0
  const processingTime = finalResults?.real_duration_minutes || finalResults?.total_processing_time_seconds / 60 || 0
  const exportedFiles = finalResults?.exported_files || []

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full mx-4 max-h-screen overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="p-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 flex items-center">
                ✨ Generation Complete!
              </h2>
              <p className="text-gray-600 mt-2">
                Successfully generated {samplesCount} synthetic samples in {processingTime.toFixed(1)} minutes
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-3xl font-light"
            >
              ×
            </button>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-green-50 border border-green-200 rounded-xl p-4 text-center">
              <div className="text-2xl font-bold text-green-700">{samplesCount}</div>
              <div className="text-sm text-green-600">Total Samples</div>
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-center">
              <div className="text-2xl font-bold text-blue-700">
                {finalResults?.pipeline_metadata?.concepts_extracted || 'N/A'}
              </div>
              <div className="text-sm text-blue-600">Concepts Used</div>
            </div>
            <div className="bg-purple-50 border border-purple-200 rounded-xl p-4 text-center">
              <div className="text-2xl font-bold text-purple-700">
                {finalResults?.pipeline_metadata?.agents_used || 5}
              </div>
              <div className="text-sm text-purple-600">AI Agents</div>
            </div>
            <div className="bg-orange-50 border border-orange-200 rounded-xl p-4 text-center">
              <div className="text-2xl font-bold text-orange-700">
                {formatFileSize(JSON.stringify(generatedSamples).length)}
              </div>
              <div className="text-sm text-orange-600">Dataset Size</div>
            </div>
          </div>

          {/* Sample Preview */}
          {generatedSamples && generatedSamples.length > 0 && (
            <div className="mb-8">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Sample Preview</h3>
              <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
                <div className="bg-white rounded-lg border p-4 text-sm font-mono max-h-60 overflow-y-auto">
                  {JSON.stringify(generatedSamples[0], null, 2)}
                </div>
              </div>
            </div>
          )}

          {/* Export Options */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Export Format</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {exportFormats.map((format) => (
                <div
                  key={format.value}
                  onClick={() => setSelectedExport(format.value)}
                  className={`p-3 rounded-lg border-2 cursor-pointer transition-all ${
                    selectedExport === format.value 
                      ? 'border-blue-500 bg-blue-50' 
                      : 'border-gray-200 bg-white hover:border-gray-300'
                  }`}
                >
                  <div className="font-semibold text-gray-900 text-sm">{format.label}</div>
                  <div className="text-xs text-gray-600">{format.description}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Exported Files */}
          {exportedFiles.length > 0 && (
            <div className="mb-8 bg-green-50 border border-green-200 rounded-xl p-4">
              <h3 className="text-lg font-semibold text-green-800 mb-3">📁 Exported Files</h3>
              <div className="space-y-2">
                {exportedFiles.map((file, index) => (
                  <div key={index} className="flex items-center justify-between bg-white rounded-lg p-3 border border-green-200">
                    <div>
                      <div className="font-medium text-gray-900 text-sm">{file.filename}</div>
                      <div className="text-xs text-gray-600">{file.format} • {file.samples_count} samples</div>
                    </div>
                    <button
                      onClick={() => window.open(`http://localhost:8000/api/datasets/download/${file.filename}`, '_blank')}
                      className="text-green-600 hover:text-green-800 text-sm font-medium"
                    >
                      Download
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center justify-center space-x-4">
            <button
              onClick={() => downloadCurrentResults(selectedExport)}
              className="bg-green-600 text-white px-6 py-3 rounded-xl hover:bg-green-700 transition-colors font-medium flex items-center"
            >
              📥 Download {selectedExport.toUpperCase()}
            </button>
            <button
              onClick={onOpenDatasets}
              className="bg-blue-600 text-white px-6 py-3 rounded-xl hover:bg-blue-700 transition-colors font-medium"
            >
              📊 View All Datasets
            </button>
            <button
              onClick={onGenerateMore}
              className="bg-purple-600 text-white px-6 py-3 rounded-xl hover:bg-purple-700 transition-colors font-medium"
            >
              🔄 Generate More
            </button>
            <button
              onClick={onReset}
              className="bg-gray-600 text-white px-6 py-3 rounded-xl hover:bg-gray-700 transition-colors font-medium"
            >
              🏠 Start Over
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ResultsModal