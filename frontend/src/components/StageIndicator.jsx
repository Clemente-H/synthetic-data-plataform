import { useState } from 'react'

const StageIndicator = ({ 
  currentStage, 
  overallProgress, 
  isProcessing, 
  isConnected, 
  error,
  progressMessage,
  progressData 
}) => {
  const [isExpanded, setIsExpanded] = useState(false)

  if (!isProcessing && !currentStage) {
    return null
  }

  const getStageDisplay = (stage) => {
    const stages = {
      'input_processing': 'Processing Input',
      'concept_extraction': 'Extracting Concepts', 
      'characterization': 'Characterizing',
      'agent_geographic': 'Geographic Agent',
      'agent_cultural': 'Cultural Agent',
      'agent_linguistic': 'Linguistic Agent',
      'agent_persona': 'Persona Agent',
      'agent_domain': 'Domain Agent',
      'human_validation': 'Validating',
      'format_selection': 'Format Selection',
      'generation': 'Generating Samples',
      'quality_assurance': 'Quality Check',
      'export': 'Finalizing'
    }
    return stages[stage] || stage?.replace(/_/g, ' ')
  }

  const getConnectionStatus = () => {
    if (error) return { color: 'bg-red-500', text: 'Error' }
    if (!isConnected) return { color: 'bg-yellow-500', text: 'Connecting' }
    if (isProcessing) return { color: 'bg-blue-500', text: 'Processing' }
    return { color: 'bg-green-500', text: 'Connected' }
  }

  const status = getConnectionStatus()

  return (
    <div className="fixed bottom-6 right-6 z-50">
      <div 
        className={`bg-white rounded-xl shadow-2xl border-2 border-gray-100 transition-all duration-300 ${
          isExpanded ? 'p-6 min-w-80' : 'p-4 min-w-48'
        }`}
        onMouseEnter={() => setIsExpanded(true)}
        onMouseLeave={() => setIsExpanded(false)}
      >
        {/* Compact View */}
        {!isExpanded && (
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className={`w-3 h-3 rounded-full ${status.color} ${isProcessing ? 'animate-pulse' : ''}`}></div>
              <div>
                <div className="text-sm font-semibold text-gray-800">
                  {isProcessing ? `${Math.round((overallProgress || 0) * 100)}%` : status.text}
                </div>
                {isProcessing && progressMessage && (
                  <div className="text-xs text-gray-600 truncate max-w-32">
                    {progressMessage}
                  </div>
                )}
              </div>
            </div>
            {isProcessing && (
              <div className="w-12 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-blue-500 transition-all duration-500"
                  style={{ width: `${Math.round((overallProgress || 0) * 100)}%` }}
                ></div>
              </div>
            )}
          </div>
        )}

        {/* Expanded View */}
        {isExpanded && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-lg font-bold text-gray-900">Pipeline Status</span>
              <div className={`w-4 h-4 rounded-full ${status.color} ${isProcessing ? 'animate-pulse' : ''} shadow-lg`}></div>
            </div>
            
            {isProcessing && (
              <>
                <div className="bg-gray-50 p-3 rounded-lg">
                  <div className="text-sm font-semibold text-gray-700 mb-1">
                    Current Stage
                  </div>
                  <div className="text-base text-gray-900">
                    {getStageDisplay(currentStage)}
                  </div>
                </div>
                
                {/* Progress message from backend */}
                {progressMessage && (
                  <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
                    <div className="text-sm font-medium text-blue-800">
                      {progressMessage}
                    </div>
                  </div>
                )}
                
                {/* Detailed progress for generation stage */}
                {currentStage === 'generation' && progressData && (
                  <div className="bg-green-50 p-3 rounded-lg border border-green-200">
                    <div className="text-sm font-semibold text-green-800 mb-2">
                      Generation Progress
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      {progressData.combination_current && progressData.combination_total && (
                        <div className="bg-white p-2 rounded">
                          <div className="font-medium text-gray-600">Combinations</div>
                          <div className="text-gray-900">
                            {progressData.combination_current.toLocaleString()} / {progressData.combination_total.toLocaleString()}
                          </div>
                        </div>
                      )}
                      {progressData.samples_generated && (
                        <div className="bg-white p-2 rounded">
                          <div className="font-medium text-gray-600">Samples</div>
                          <div className="text-gray-900">{progressData.samples_generated.toLocaleString()}</div>
                        </div>
                      )}
                      {progressData.current_batch && progressData.total_batches && (
                        <div className="bg-white p-2 rounded col-span-2">
                          <div className="font-medium text-gray-600">GPU Batches</div>
                          <div className="text-gray-900">
                            {progressData.current_batch} / {progressData.total_batches} (Parallel Processing)
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                
                {overallProgress !== undefined && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium text-gray-700">Overall Progress</span>
                      <span className="font-bold text-gray-900">
                        {Math.round((overallProgress || 0) * 100)}%
                      </span>
                    </div>
                    <div className="bg-gray-200 rounded-full h-3 overflow-hidden">
                      <div 
                        className="bg-gradient-to-r from-blue-500 to-green-500 h-3 rounded-full transition-all duration-500 shadow-sm"
                        style={{ width: `${Math.round((overallProgress || 0) * 100)}%` }}
                      ></div>
                    </div>
                  </div>
                )}
              </>
            )}

            {error && (
              <div className="text-xs text-red-600 bg-red-50 p-2 rounded">
                {error.length > 50 ? error.substring(0, 50) + '...' : error}
              </div>
            )}

            {!isProcessing && !error && (
              <div className="text-xs text-green-600">
                Ready
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default StageIndicator