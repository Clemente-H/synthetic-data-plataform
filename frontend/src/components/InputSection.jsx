import { useState, useRef } from 'react'

const InputSection = ({ onTextSubmit, isProcessing, currentStep }) => {
  const [inputText, setInputText] = useState('')
  const [hasFile, setHasFile] = useState(false)
  const fileInputRef = useRef(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (inputText.trim() && !isProcessing) {
      await onTextSubmit(inputText.trim())
    }
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (file && !isProcessing) {
      const text = await file.text()
      setInputText(text)
      setHasFile(true)
    }
  }

  const handleDrop = async (e) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file && !isProcessing) {
      const text = await file.text()
      setInputText(text)
      setHasFile(true)
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
  }

  if (currentStep > 2) return null

  return (
    <div className={`bg-white border-radius-16 shadow-lg p-8 text-center transition-all duration-300 ${
      isProcessing ? 'animate-pulse-refined' : ''
    }`}>
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          Input Your Data
        </h2>
        <p className="text-gray-600">
          Enter text directly or upload a document to extract concepts
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* File Upload Area */}
        <div
          className={`border-3 border-dashed rounded-xl p-8 cursor-pointer transition-all duration-300 ${
            hasFile
              ? 'border-primary-500 bg-primary-50'
              : 'border-gray-300 bg-gray-50 hover:border-primary-500 hover:bg-primary-50'
          } ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}`}
          onClick={() => !isProcessing && fileInputRef.current?.click()}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".txt,.md,.doc,.docx"
            onChange={handleFileUpload}
            className="hidden"
            disabled={isProcessing}
          />
          
          <div className="space-y-2">
            <div className="text-3xl text-gray-400">
              {hasFile ? '✓' : '⬆'}
            </div>
            <div className="text-lg font-medium text-gray-700">
              {hasFile ? 'File loaded' : 'Drop file here or click to upload'}
            </div>
            <div className="text-sm text-gray-500">
              Supports .txt, .md, .doc, .docx files
            </div>
          </div>
        </div>

        {/* Text Input */}
        <div className="text-left">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Or enter text directly:
          </label>
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Describe your domain, process, or use case. The more detailed, the better the concept extraction..."
            className="w-full h-32 p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none"
            disabled={isProcessing}
          />
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={!inputText.trim() || isProcessing}
          className={`w-full py-3 px-6 rounded-lg font-medium transition-all duration-200 ${
            isProcessing
              ? 'bg-gray-400 text-white cursor-not-allowed'
              : inputText.trim()
              ? 'bg-primary-600 text-white hover:bg-primary-700 hover:shadow-md transform hover:scale-105'
              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
          }`}
        >
          {isProcessing ? (
            <div className="flex items-center justify-center space-x-2">
              <div className="animate-breathing">
                <div className="w-2 h-2 bg-white rounded-full"></div>
              </div>
              <span>Extracting concepts...</span>
            </div>
          ) : (
            'Extract Concepts'
          )}
        </button>
      </form>

      {/* Processing Indicator */}
      {isProcessing && currentStep === 2 && (
        <div className="mt-6 p-4 bg-primary-50 rounded-lg border border-primary-200">
          <div className="flex items-center justify-center space-x-2 text-primary-700">
            <div className="animate-breathing w-3 h-3 bg-primary-600 rounded-full"></div>
            <span className="text-sm font-medium">AI is analyzing your text...</span>
          </div>
        </div>
      )}
    </div>
  )
}

export default InputSection