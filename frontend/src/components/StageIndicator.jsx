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
    <div className="fixed bottom-4 right-4 z-50">
      <div 
        className={`bg-white rounded-lg shadow-lg border transition-all duration-300 ${
          isExpanded ? 'p-4 min-w-64' : 'p-3'
        }`}
        onMouseEnter={() => setIsExpanded(true)}
        onMouseLeave={() => setIsExpanded(false)}
      >
        {/* Compact View */}
        {!isExpanded && (
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${status.color} ${isProcessing ? 'animate-pulse' : ''}`}></div>
            <span className="text-xs font-medium text-gray-700">
              {isProcessing ? Math.round((overallProgress || 0) * 100) + '%' : status.text}
            </span>
          </div>
        )}

        {/* Expanded View */}
        {isExpanded && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-900">Pipeline Status</span>
              <div className={`w-2 h-2 rounded-full ${status.color} ${isProcessing ? 'animate-pulse' : ''}`}></div>
            </div>
            
            {isProcessing && (
              <>
                <div className="text-xs text-gray-600">
                  {getStageDisplay(currentStage)}
                </div>
                
                {/* Progress message from backend */}
                {progressMessage && (
                  <div className="text-xs text-blue-600 font-medium">
                    {progressMessage}
                  </div>
                )}
                
                {/* Detailed progress for generation stage */}
                {currentStage === 'generation' && progressData && (
                  <div className="space-y-1 text-xs text-gray-600">
                    {progressData.combination_current && progressData.combination_total && (
                      <div>
                        Combination: {progressData.combination_current.toLocaleString()} / {progressData.combination_total.toLocaleString()}
                      </div>
                    )}
                    {progressData.samples_generated && (
                      <div>
                        Samples: {progressData.samples_generated.toLocaleString()}
                      </div>
                    )}
                    {progressData.current_batch && progressData.total_batches && (
                      <div>
                        Batch: {progressData.current_batch} / {progressData.total_batches} (GPU Parallel)
                      </div>
                    )}
                    {progressData.combination_id && (
                      <div className="text-gray-400">
                        ID: {progressData.combination_id}
                      </div>
                    )}
                  </div>
                )}
                
                {overallProgress !== undefined && (
                  <div className="space-y-1">
                    <div className="bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-primary-600 h-2 rounded-full transition-all duration-500"
                        style={{ width: `${Math.round((overallProgress || 0) * 100)}%` }}
                      ></div>
                    </div>
                    <div className="text-xs text-gray-500 text-right">
                      {Math.round((overallProgress || 0) * 100)}%
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