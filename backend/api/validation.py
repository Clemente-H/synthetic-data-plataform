#!/usr/bin/env python3
"""
Validation API - Step 4: Human Validation + Customization Interface
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

# Request/Response Models
class ConceptValidationRequest(BaseModel):
    concepts: List[str] = Field(..., description="Concepts to validate")
    category: str = Field(..., description="Category of concepts (geographic, cultural, etc.)")
    user_additions: List[str] = Field(default=[], description="User-added concepts")
    user_removals: List[str] = Field(default=[], description="User-removed concepts")

class ValidationResponse(BaseModel):
    validated_concepts: List[str]
    total_concepts: int
    user_modifications: Dict[str, int]
    validation_timestamp: str

class CombinationPreviewRequest(BaseModel):
    concept_dimensions: Dict[str, List[str]] = Field(..., description="All concept dimensions")
    preview_limit: int = Field(10, description="Number of combinations to preview", ge=1, le=50)

class CombinationPreview(BaseModel):
    combination_id: str
    concepts: Dict[str, str]
    complexity_level: int
    estimated_samples: int

class PreviewResponse(BaseModel):
    preview_combinations: List[CombinationPreview]
    total_possible_combinations: int
    estimated_total_samples: int
    generation_feasibility: str

@router.post("/validate-concepts", response_model=ValidationResponse)
async def validate_concepts(request: ConceptValidationRequest):
    """
    Step 4: Human Validation + Customization
    
    Allows users to review, modify, and expand generated concept lists
    while maintaining workflow efficiency
    """
    try:
        logger.info(f"🔍 Validating {len(request.concepts)} concepts for category: {request.category}")
        
        # Start with AI-generated concepts
        working_concepts = request.concepts.copy()
        
        # Apply user removals
        if request.user_removals:
            working_concepts = [c for c in working_concepts if c not in request.user_removals]
            logger.info(f"Removed {len(request.user_removals)} user-specified concepts")
        
        # Apply user additions (with basic validation)
        validated_additions = []
        if request.user_additions:
            for addition in request.user_additions:
                if isinstance(addition, str) and len(addition.strip()) > 2:
                    clean_addition = addition.strip()
                    if clean_addition not in working_concepts:
                        validated_additions.append(clean_addition)
            
            working_concepts.extend(validated_additions)
            logger.info(f"Added {len(validated_additions)} user-specified concepts")
        
        # Remove duplicates while preserving order
        final_concepts = []
        seen = set()
        for concept in working_concepts:
            if concept not in seen:
                final_concepts.append(concept)
                seen.add(concept)
        
        validation_metadata = {
            "original_count": len(request.concepts),
            "user_additions_count": len(validated_additions),
            "user_removals_count": len(request.user_removals),
            "final_count": len(final_concepts)
        }
        
        logger.info(f"✅ Validation complete: {len(final_concepts)} final concepts")
        
        return ValidationResponse(
            validated_concepts=final_concepts,
            total_concepts=len(final_concepts),
            user_modifications=validation_metadata,
            validation_timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"❌ Concept validation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Concept validation failed: {str(e)}"
        )

@router.post("/preview-combinations", response_model=PreviewResponse)
async def preview_combinations(request: CombinationPreviewRequest):
    """
    Preview concept combinations before generation
    
    Shows users a sample of combinations that will be generated
    to help them understand the scope and adjust parameters
    """
    try:
        from core.combinator import ConceptCombinator
        
        logger.info(f"🔮 Generating combination preview (limit: {request.preview_limit})")
        
        # Initialize combinator for preview
        combinator = ConceptCombinator()
        
        # Generate preview combinations
        preview_combinations = combinator.preview_combinations(
            request.concept_dimensions,
            limit=request.preview_limit
        )
        
        # Estimate total scale
        estimated_samples, stats = combinator.estimate_total_samples(
            request.concept_dimensions,
            samples_per_combination=3  # Default for estimation
        )
        
        # Convert to response format
        preview_items = []
        for i, combo in enumerate(preview_combinations):
            preview_items.append(CombinationPreview(
                combination_id=combo.get('combination_id', f'preview_{i}'),
                concepts={k: v for k, v in combo.items() if k != 'combination_id' and k != 'complexity_level'},
                complexity_level=combo.get('complexity_level', 1),
                estimated_samples=3  # Default samples per combination for preview
            ))
        
        # Determine feasibility
        if estimated_samples < 1000:
            feasibility = "small_scale"
        elif estimated_samples < 10000:
            feasibility = "medium_scale"
        elif estimated_samples < 50000:
            feasibility = "large_scale"
        else:
            feasibility = "massive_scale"
        
        logger.info(f"✅ Preview generated: {len(preview_items)} combinations, {estimated_samples:,} estimated samples")
        
        return PreviewResponse(
            preview_combinations=preview_items,
            total_possible_combinations=stats["total_combinations"],
            estimated_total_samples=estimated_samples,
            generation_feasibility=feasibility
        )
        
    except Exception as e:
        logger.error(f"❌ Combination preview failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Combination preview failed: {str(e)}"
        )

@router.post("/validate-generation-params")
async def validate_generation_parameters(
    concept_dimensions: Dict[str, List[str]],
    format_type: str,
    samples_per_combination: int = 3,
    max_total_samples: int = 10000
):
    """
    Validate generation parameters before starting generation
    
    Helps users understand the scope and adjust parameters appropriately
    """
    try:
        from core.combinator import ConceptCombinator
        
        logger.info("🧮 Validating generation parameters")
        
        # Validation checks
        validation_results = {
            "is_valid": True,
            "warnings": [],
            "recommendations": [],
            "parameter_analysis": {}
        }
        
        # Check concept dimensions
        active_dimensions = {k: v for k, v in concept_dimensions.items() if v}
        if len(active_dimensions) < 2:
            validation_results["warnings"].append("Consider using at least 2 concept dimensions for diversity")
        
        # Estimate scale
        combinator = ConceptCombinator()
        estimated_samples, stats = combinator.estimate_total_samples(
            concept_dimensions,
            samples_per_combination
        )
        
        validation_results["parameter_analysis"] = {
            "active_dimensions": len(active_dimensions),
            "total_concepts": sum(len(concepts) for concepts in active_dimensions.values()),
            "estimated_combinations": stats["total_combinations"],
            "estimated_samples": estimated_samples,
            "samples_per_combination": samples_per_combination,
            "format_type": format_type
        }
        
        # Recommendations based on scale
        if estimated_samples > max_total_samples:
            validation_results["warnings"].append(
                f"Estimated samples ({estimated_samples:,}) exceed limit ({max_total_samples:,})"
            )
            validation_results["recommendations"].append("Consider reducing samples_per_combination or limiting concept selections")
        
        if estimated_samples < 100:
            validation_results["recommendations"].append("Consider adding more concepts or increasing samples_per_combination for richer dataset")
        
        if format_type not in ["dpo", "sft", "qa", "raw"]:
            validation_results["is_valid"] = False
            validation_results["warnings"].append(f"Unsupported format: {format_type}")
        
        # Processing time estimates
        if estimated_samples < 1000:
            processing_estimate = "1-5 minutes"
        elif estimated_samples < 10000:
            processing_estimate = "10-30 minutes"
        else:
            processing_estimate = "30+ minutes"
        
        validation_results["parameter_analysis"]["estimated_processing_time"] = processing_estimate
        
        logger.info(f"✅ Parameter validation complete: {estimated_samples:,} samples estimated")
        
        return {
            "validation_results": validation_results,
            "generation_feasible": validation_results["is_valid"],
            "scale_category": _get_scale_category(estimated_samples)
        }
        
    except Exception as e:
        logger.error(f"❌ Parameter validation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Parameter validation failed: {str(e)}"
        )

def _get_scale_category(estimated_samples: int) -> str:
    """Categorize generation scale"""
    if estimated_samples < 1000:
        return "small"
    elif estimated_samples < 10000:
        return "medium" 
    elif estimated_samples < 50000:
        return "large"
    else:
        return "massive"

@router.post("/suggest-additional-concepts")
async def suggest_additional_concepts(
    category: str,
    existing_concepts: List[str],
    core_concepts: List[str] = [],
    max_suggestions: int = 10
):
    """
    AI-powered suggestions for additional concepts in a category
    
    Helps users expand their concept lists with AI suggestions
    """
    try:
        logger.info(f"🤖 Generating additional concept suggestions for {category}")
        
        # Import appropriate agent
        agent_map = {
            'geographic': 'agents.geographic_agent.GeographicAgent',
            'cultural': 'agents.cultural_agent.CulturalAgent', 
            'linguistic': 'agents.linguistic_agent.LinguisticAgent',
            'persona': 'agents.persona_agent.PersonaAgent',
            'domain': 'agents.domain_agent.DomainAgent'
        }
        
        if category not in agent_map:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported category: {category}. Available: {list(agent_map.keys())}"
            )
        
        # Get agent suggestions (simplified for this endpoint)
        # In production, you'd instantiate the appropriate agent
        suggestions = await _get_category_suggestions(category, core_concepts, existing_concepts, max_suggestions)
        
        # Filter out existing concepts
        new_suggestions = [s for s in suggestions if s not in existing_concepts]
        
        logger.info(f"✅ Generated {len(new_suggestions)} new suggestions for {category}")
        
        return {
            "category": category,
            "new_suggestions": new_suggestions[:max_suggestions],
            "existing_concepts_count": len(existing_concepts),
            "suggestion_source": "ai_agent"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Additional concept suggestion failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Suggestion generation failed: {str(e)}"
        )

async def _get_category_suggestions(category: str, core_concepts: List[str], 
                                  existing_concepts: List[str], max_suggestions: int) -> List[str]:
    """
    Get suggestions for a specific category (simplified implementation)
    """
    # For demo purposes, return category-appropriate suggestions
    # In production, this would use the actual agents
    
    suggestion_map = {
        'geographic': [
            "North America", "Europe", "Asia Pacific", "Latin America", "Middle East",
            "Urban Centers", "Rural Areas", "Developing Markets", "Emerging Economies"
        ],
        'cultural': [
            "Traditional Values", "Modern Lifestyle", "Multicultural", "Youth Culture",
            "Professional Culture", "Academic Environment", "Creative Community"
        ],
        'linguistic': [
            "Formal Communication", "Casual Style", "Technical Language", "Plain Language",
            "Multilingual Context", "Business Communication", "Academic Writing"
        ],
        'persona': [
            "Expert User", "Beginner", "Business Professional", "Student", "Researcher",
            "Decision Maker", "Technical Specialist", "General Consumer"
        ],
        'domain': [
            "Technical Documentation", "Best Practices", "Industry Standards", "Compliance",
            "Innovation", "Research & Development", "Implementation Guidelines"
        ]
    }
    
    base_suggestions = suggestion_map.get(category, [])
    return base_suggestions[:max_suggestions]

@router.get("/health")
async def validation_health():
    """Health check for validation service"""
    return {
        "status": "healthy",
        "service": "human_validation_interface",
        "capabilities": [
            "Concept validation and customization",
            "Combination preview generation", 
            "Parameter validation and recommendations",
            "AI-powered concept suggestions",
            "Generation feasibility analysis"
        ],
        "supported_categories": ["geographic", "cultural", "linguistic", "persona", "domain"]
    }