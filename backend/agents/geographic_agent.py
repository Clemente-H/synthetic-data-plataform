#!/usr/bin/env python3
"""
Geographic Agent - Identifies location-specific contexts and regional variations
"""

from typing import List, Dict, Any
import logging
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class GeographicAgent(BaseAgent):
    """
    Specialized agent for geographic context characterization
    Identifies location-specific regulations, cultural norms, legal frameworks,
    and regional business practices
    """
    
    def __init__(self):
        super().__init__("geographic")
    
    async def process(self, core_concepts: List[str], 
                     additional_context: Dict[str, List[str]] = None) -> List[str]:
        """
        Generate geographic contexts based on core concepts
        """
        logger.info(f"Processing geographic contexts for concepts: {core_concepts}")
        
        # Generate AI-powered geographic suggestions
        suggestions = await self._generate_suggestions(
            core_concepts, 
            additional_context,
            max_suggestions=15
        )
        
        # Enhance with domain-specific geographic considerations
        enhanced_suggestions = self._enhance_with_domain_specific_geography(
            core_concepts, 
            suggestions
        )
        
        # Validate and return
        validated = self.validate_suggestions(enhanced_suggestions)
        return validated[:15]
    
    def _enhance_with_domain_specific_geography(self, core_concepts: List[str], 
                                               base_suggestions: List[str]) -> List[str]:
        """
        Add domain-specific geographic contexts based on concepts
        """
        concept_text = " ".join(core_concepts).lower()
        enhanced = base_suggestions.copy()
        
        # Healthcare-specific geography
        if any(term in concept_text for term in ['health', 'medical', 'healthcare', 'patient']):
            healthcare_geo = [
                "US Healthcare System",
                "NHS (United Kingdom)", 
                "Canadian Universal Healthcare",
                "German Healthcare Model",
                "Japanese Healthcare System",
                "Scandinavian Healthcare",
                "Rural Healthcare Access",
                "Urban Medical Centers"
            ]
            enhanced.extend([geo for geo in healthcare_geo if geo not in enhanced])
        
        # Technology-specific geography  
        if any(term in concept_text for term in ['tech', 'software', 'ai', 'digital']):
            tech_geo = [
                "Silicon Valley",
                "European Tech Hubs",
                "Asian Tech Centers", 
                "GDPR Compliance (EU)",
                "Chinese Tech Regulations",
                "Indian IT Services",
                "Israeli Tech Ecosystem",
                "Canadian Tech Scene"
            ]
            enhanced.extend([geo for geo in tech_geo if geo not in enhanced])
        
        # Financial services geography
        if any(term in concept_text for term in ['finance', 'banking', 'investment', 'money']):
            finance_geo = [
                "Wall Street (US)",
                "City of London",
                "Hong Kong Financial Hub",
                "Swiss Banking",
                "Singapore Financial Center",
                "Tokyo Stock Exchange",
                "European Banking Union",
                "Offshore Financial Centers"
            ]
            enhanced.extend([geo for geo in finance_geo if geo not in enhanced])
        
        # Education-specific geography
        if any(term in concept_text for term in ['education', 'university', 'student', 'learning']):
            education_geo = [
                "US Higher Education",
                "British University System",
                "European Bologna Process",
                "Asian Education Systems",
                "Nordic Education Model",
                "Australian Universities",
                "Online Global Education",
                "Developing World Education"
            ]
            enhanced.extend([geo for geo in education_geo if geo not in enhanced])
        
        return enhanced
    
    def _get_fallback_suggestions(self) -> List[str]:
        """
        Fallback geographic suggestions covering major world regions
        """
        return [
            "United States",
            "European Union", 
            "United Kingdom",
            "Canada",
            "Australia",
            "Japan",
            "South Korea",
            "Singapore", 
            "Brazil",
            "Mexico",
            "India",
            "China",
            "Southeast Asia",
            "Middle East",
            "Nordic Countries"
        ]