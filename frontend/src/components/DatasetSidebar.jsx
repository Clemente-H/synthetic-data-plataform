import { useState, useEffect } from 'react'

const DatasetSidebar = ({ isOpen, onClose, finalResults, generatedSamples }) => {
  const [datasets, setDatasets] = useState([])
  const [loadingDatasets, setLoadingDatasets] = useState(false)
  const [downloadingFile, setDownloadingFile] = useState(null)

  // Load available datasets from backend
  const loadDatasets = async () => {
    setLoadingDatasets(true)
    try {
      const response = await fetch('http://localhost:8000/api/datasets/list')
      if (response.ok) {
        const data = await response.json()
        setDatasets(data.datasets || [])
      }
    } catch (error) {
      console.error('Failed to load datasets:', error)
    } finally {
      setLoadingDatasets(false)
    }
  }

  // Download dataset file
  const downloadDataset = async (filename) => {
    setDownloadingFile(filename)
    try {
      const downloadUrl = `http://localhost:8000/api/datasets/download/${filename}`
      window.open(downloadUrl, '_blank')
    } catch (error) {
      console.error('Failed to download dataset:', error)
    } finally {
      setDownloadingFile(null)
    }
  }

  // Download current results as JSON
  const downloadCurrentResults = () => {
    if (!generatedSamples || generatedSamples.length === 0) return
    
    const dataStr = JSON.stringify(generatedSamples, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `synthetic-dataset-${new Date().toISOString().slice(0, 10)}.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  // Load datasets when sidebar opens
  useEffect(() => {
    if (isOpen) {
      loadDatasets()
    }
  }, [isOpen])

  // Refresh datasets when new results arrive
  useEffect(() => {
    if (finalResults && isOpen) {
      setTimeout(loadDatasets, 1000) // Refresh after 1s to let backend save
    }
  }, [finalResults, isOpen])

  // Format file size
  const formatFileSize = (bytes) => {
    if (!bytes) return '0 KB'
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return Math.round(bytes / 1024) + ' KB'
    return Math.round(bytes / (1024 * 1024)) + ' MB'
  }

  // Format date
  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown'
    try {
      return new Date(dateString).toLocaleString()
    } catch {
      return dateString
    }
  }

  if (!isOpen) return null

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-25 z-40"
        onClick={onClose}
      />
      
      {/* Sidebar */}
      <div className="fixed right-0 top-0 h-full w-96 bg-white shadow-2xl z-50 transform transition-transform duration-300 overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-900">
              Generated Datasets
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl"
            >
              ×
            </button>
          </div>

          {/* Current Results */}
          {generatedSamples && generatedSamples.length > 0 && (
            <div className="mb-6 p-4 bg-gradient-to-r from-green-50 to-blue-50 rounded-lg border border-green-200">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-gray-800">
                  ✨ Latest Results
                </h3>
                <span className="text-sm text-green-600 font-medium">
                  {generatedSamples.length} samples
                </span>
              </div>
              
              <div className="space-y-2 text-sm text-gray-600 mb-4">
                <div>Format: {finalResults?.format_type || 'Unknown'}</div>
                <div>
                  Size: {formatFileSize(JSON.stringify(generatedSamples).length)}
                </div>
                <div>Generated: {new Date().toLocaleString()}</div>
              </div>

              <button
                onClick={downloadCurrentResults}
                className="w-full bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors font-medium text-sm"
              >
                📥 Download JSON
              </button>
            </div>
          )}

          {/* Saved Datasets */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-800">
                Saved Datasets
              </h3>
              <button
                onClick={loadDatasets}
                disabled={loadingDatasets}
                className="text-sm text-blue-600 hover:text-blue-800 disabled:text-gray-400"
              >
                {loadingDatasets ? '🔄' : '↻'} Refresh
              </button>
            </div>

            {loadingDatasets ? (
              <div className="text-center py-8 text-gray-500">
                <div className="inline-block w-6 h-6 border-2 border-gray-300 border-t-blue-600 rounded-full animate-spin mb-2"></div>
                <div>Loading datasets...</div>
              </div>
            ) : datasets.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <div className="text-4xl mb-2">📂</div>
                <div>No datasets found</div>
                <div className="text-sm">Generate some data to see it here</div>
              </div>
            ) : (
              <div className="space-y-3">
                {datasets.map((dataset, index) => (
                  <div
                    key={dataset.filename || index}
                    className="border border-gray-200 rounded-lg p-3 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="font-medium text-gray-800 text-sm truncate flex-1">
                        {dataset.filename || `dataset-${index}`}
                      </div>
                      <button
                        onClick={() => downloadDataset(dataset.filename)}
                        disabled={downloadingFile === dataset.filename}
                        className="ml-2 text-blue-600 hover:text-blue-800 text-sm disabled:text-gray-400"
                      >
                        {downloadingFile === dataset.filename ? '⬇️' : '📥'}
                      </button>
                    </div>
                    
                    <div className="space-y-1 text-xs text-gray-600">
                      <div className="flex justify-between">
                        <span>Format:</span>
                        <span className="capitalize">{dataset.format || 'Unknown'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Size:</span>
                        <span>{formatFileSize(dataset.size)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Samples:</span>
                        <span>{dataset.samples_count || 'Unknown'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Created:</span>
                        <span>{formatDate(dataset.created_at)}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Help */}
          <div className="mt-8 p-3 bg-gray-50 rounded-lg text-sm text-gray-600">
            <div className="font-medium mb-1">💡 Tip</div>
            <div>
              Datasets are automatically saved after generation. 
              You can download them anytime from here.
            </div>
          </div>
        </div>
      </div>
    </>
  )
}

export default DatasetSidebar