import React, { useState } from 'react';

/**
 * ConceptContainer - Reusable component for displaying concepts
 * Adapts layout and styling based on stage (core concepts vs categories)
 */
const ConceptContainer = ({
  title,
  concepts = [],
  layout = 'row', // 'row' for core concepts, 'column' for categories
  style = 'primary', // 'primary' | 'secondary'
  showRemoveX = true,
  onToggle = () => {},
  onRemove = () => {},
  onComplete = () => {},
  loading = false,
  showCompleteButton = false,
  className = ''
}) => {
  const [selectedConcepts, setSelectedConcepts] = useState([])

  const handleConceptClick = (concept) => {
    if (layout === 'row') {
      // For core concepts, toggle selection
      setSelectedConcepts(prev => 
        prev.includes(concept)
          ? prev.filter(c => c !== concept)
          : [...prev, concept]
      )
    }
    onToggle(concept)
  }

  const handleComplete = () => {
    if (layout === 'row') {
      // For core concepts, pass selected concepts
      onComplete(selectedConcepts.length > 0 ? selectedConcepts : concepts)
    } else {
      onComplete(concepts)
    }
  }
  const baseClasses = `
    bg-white rounded-lg shadow-sm border transition-all duration-300
    ${loading ? 'animate-pulse' : ''}
    ${className}
  `;

  const titleClasses = `
    font-semibold mb-3 flex items-center justify-between
    ${style === 'primary' ? 'text-lg text-gray-900' : 'text-md text-gray-800'}
  `;

  const conceptsContainerClasses = `
    ${layout === 'row' 
      ? 'flex flex-wrap gap-2 justify-center' // Core concepts in row
      : 'flex flex-col gap-2' // Categories in column
    }
  `;

  const getConceptItemClasses = (concept, isSelected = false) => `
    px-3 py-2 rounded-full border cursor-pointer transition-all duration-200
    flex items-center gap-2 text-sm font-medium
    ${style === 'primary' 
      ? isSelected
        ? 'bg-primary-100 border-primary-300 text-primary-900'
        : 'bg-primary-50 border-primary-200 text-primary-800 hover:bg-primary-100' 
      : 'bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100'
    }
    hover:shadow-sm transform hover:scale-105
  `;

  const removeButtonClasses = `
    ml-2 w-4 h-4 rounded-full bg-red-500 text-white text-xs 
    flex items-center justify-center hover:bg-red-600 transition-colors
  `;

  const pulsingClasses = loading ? 'animate-pulse opacity-60' : '';

  return (
    <div className={`${baseClasses} ${pulsingClasses} p-4`}>
      {/* Title Section */}
      <div className={titleClasses}>
        <span>{title}</span>
        {concepts.length > 0 && (
          <span className="text-sm text-gray-500 font-normal">
            {concepts.length} selected
          </span>
        )}
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin w-8 h-8 border-4 border-green-200 border-t-green-600 rounded-full"></div>
          <span className="ml-3 text-gray-600">Generating concepts...</span>
        </div>
      )}

      {/* Concepts Display */}
      {!loading && concepts.length > 0 && (
        <div className={conceptsContainerClasses}>
          {concepts.map((concept, index) => {
            const isSelected = layout === 'row' && selectedConcepts.includes(concept)
            return (
              <div
                key={`${concept}-${index}`}
                className={getConceptItemClasses(concept, isSelected)}
                onClick={() => handleConceptClick(concept)}
              >
                <span>{concept}</span>
                {showRemoveX && (
                  <button
                    className={removeButtonClasses}
                    onClick={(e) => {
                      e.stopPropagation();
                      onRemove(concept);
                    }}
                  >
                    ×
                  </button>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Complete Button */}
      {showCompleteButton && !loading && concepts.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <button
            onClick={handleComplete}
            className="w-full bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors font-medium"
          >
            Continue with {layout === 'row' && selectedConcepts.length > 0 ? selectedConcepts.length : concepts.length} concepts
          </button>
        </div>
      )}

      {/* Empty State */}
      {!loading && concepts.length === 0 && (
        <div className="text-center py-6 text-gray-500">
          <div className="text-2xl mb-2">•</div>
          <p>No concepts available yet</p>
        </div>
      )}

      {/* Layout-specific styling for columns */}
      {layout === 'column' && (
        <style jsx>{`
          .concept-column {
            max-height: 300px;
            overflow-y: auto;
          }
        `}</style>
      )}
    </div>
  );
};

export default ConceptContainer;