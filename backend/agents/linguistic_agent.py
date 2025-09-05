#!/usr/bin/env python3
"""
Linguistic Agent - Extracts language variations, terminology, and communication styles
"""

from typing import List, Dict, Any
import logging
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class LinguisticAgent(BaseAgent):
    """
    Specialized agent for linguistic context characterization
    Extracts language variations, technical terminology, formality levels,
    and communication styles appropriate to the domain
    """
    
    def __init__(self):
        super().__init__("linguistic")
    
    async def process(self, core_concepts: List[str], 
                     additional_context: Dict[str, List[str]] = None) -> List[str]:
        """
        Generate linguistic contexts based on core concepts and geographic context
        """
        logger.info(f"Processing linguistic contexts for concepts: {core_concepts}")
        
        # Generate AI-powered linguistic suggestions
        ai_suggestions = await self._generate_suggestions(
            core_concepts, 
            additional_context,
            max_suggestions=10
        )
        
        # Add formality and style variations
        style_variations = self._get_communication_style_variations()
        
        # Add language and dialect variations based on geographic context
        language_variations = self._get_language_variations(additional_context)
        
        # Add domain-specific terminology styles
        terminology_styles = self._get_domain_terminology_styles(core_concepts)
        
        # Combine all suggestions
        all_suggestions = ai_suggestions + style_variations + language_variations + terminology_styles
        unique_suggestions = list(dict.fromkeys(all_suggestions))
        
        # Validate and return
        validated = self.validate_suggestions(unique_suggestions)
        return validated[:15]
    
    def _get_communication_style_variations(self) -> List[str]:
        """
        Generate different communication styles and formality levels
        """
        return [
            "Formal Professional",
            "Casual Conversational",
            "Technical/Scientific",
            "Academic Writing Style",
            "Business Communication",
            "Friendly/Approachable",
            "Authoritative/Expert",
            "Empathetic/Supportive",
            "Direct/Concise",
            "Detailed/Comprehensive"
        ]
    
    def _get_language_variations(self, additional_context: Dict[str, List[str]] = None) -> List[str]:
        """
        Generate language and dialect variations based on geographic context
        """
        variations = [
            "Standard American English",
            "British English",
            "International English",
            "Simplified Language (ESL-friendly)"
        ]
        
        # Add specific variations based on geographic context
        if additional_context and 'geographic' in additional_context:
            geo_contexts = additional_context['geographic']
            geo_text = " ".join(geo_contexts).lower()
            
            if any(region in geo_text for region in ['latin', 'spanish', 'mexico', 'brazil']):
                variations.extend([
                    "Spanish Language Context",
                    "Portuguese Language Context",
                    "Bilingual Spanish-English"
                ])
            
            if any(region in geo_text for region in ['europe', 'france', 'germany']):
                variations.extend([
                    "European English Style",
                    "Multilingual European Context"
                ])
            
            if any(region in geo_text for region in ['asia', 'china', 'japan', 'korea']):
                variations.extend([
                    "Asian English Patterns",
                    "Cross-cultural Communication"
                ])
        
        return variations
    
    def _get_domain_terminology_styles(self, core_concepts: List[str]) -> List[str]:
        """
        Generate terminology styles based on domain concepts
        """
        concept_text = " ".join(core_concepts).lower()
        styles = []
        
        # Healthcare terminology
        if any(term in concept_text for term in ['health', 'medical', 'patient']):
            styles.extend([
                "Medical Terminology",
                "Patient-Friendly Language",
                "Clinical Documentation Style",
                "Health Education Language"
            ])
        
        # Technology terminology
        if any(term in concept_text for term in ['tech', 'software', 'ai']):
            styles.extend([
                "Technical Documentation",
                "Developer-to-Developer",
                "Non-Technical Explanation",
                "API Documentation Style"
            ])
        
        # Business terminology
        if any(term in concept_text for term in ['business', 'finance', 'management']):
            styles.extend([
                "Business Jargon",
                "Executive Summary Style",
                "Financial Reporting Language",
                "Corporate Communication"
            ])
        
        # Education terminology
        if any(term in concept_text for term in ['education', 'learning', 'academic']):
            styles.extend([
                "Academic Language",
                "Student-Friendly Explanations",
                "Educational Content Style",
                "Curriculum Description Language"
            ])
        
        return styles
    
    def _get_fallback_suggestions(self) -> List[str]:
        """
        Fallback linguistic suggestions covering common styles
        """
        return [
            "Professional Tone",
            "Conversational Style",
            "Technical Language",
            "Plain Language",
            "Formal Documentation",
            "Informal Communication",
            "Instructional Style",
            "Explanatory Tone",
            "Question-Answer Format",
            "Step-by-Step Language",
            "Comparative Language",
            "Descriptive Style",
            "Analytical Tone",
            "Narrative Style",
            "Concise Communication"
        ]