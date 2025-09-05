#!/usr/bin/env python3
"""
Persona Agent - Generates diverse user archetypes and demographic variations
"""

from typing import List, Dict, Any
import logging
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class PersonaAgent(BaseAgent):
    """
    Specialized agent for persona context characterization
    Generates diverse user archetypes, expertise levels, demographic considerations,
    and role-specific perspectives
    """
    
    def __init__(self):
        super().__init__("persona")
    
    async def process(self, core_concepts: List[str], 
                     additional_context: Dict[str, List[str]] = None) -> List[str]:
        """
        Generate persona contexts based on core concepts and other dimensions
        """
        logger.info(f"Processing persona contexts for concepts: {core_concepts}")
        
        # Generate AI-powered persona suggestions
        ai_suggestions = await self._generate_suggestions(
            core_concepts, 
            additional_context,
            max_suggestions=12
        )
        
        # Add domain-specific personas
        domain_personas = self._get_domain_specific_personas(core_concepts)
        
        # Add demographic variations
        demographic_personas = self._get_demographic_variations(core_concepts)
        
        # Combine all suggestions
        all_suggestions = ai_suggestions + domain_personas + demographic_personas
        unique_suggestions = list(dict.fromkeys(all_suggestions))
        
        # Validate and return
        validated = self.validate_suggestions(unique_suggestions)
        return validated[:15]
    
    def _get_domain_specific_personas(self, core_concepts: List[str]) -> List[str]:
        """
        Generate personas specific to the domain of the concepts
        """
        concept_text = " ".join(core_concepts).lower()
        personas = []
        
        # Healthcare personas
        if any(term in concept_text for term in ['health', 'medical', 'patient', 'doctor']):
            personas.extend([
                "Experienced Doctor",
                "New Medical Graduate", 
                "Concerned Patient",
                "Elderly Patient",
                "Pediatric Patient Parent",
                "Healthcare Administrator",
                "Medical Researcher",
                "Nurse Practitioner"
            ])
        
        # Technology personas
        if any(term in concept_text for term in ['tech', 'software', 'ai', 'digital']):
            personas.extend([
                "Senior Software Developer",
                "Junior Developer", 
                "Tech-Savvy User",
                "Non-Technical User",
                "IT Administrator",
                "Product Manager",
                "UX Designer",
                "Data Scientist"
            ])
        
        # Education personas
        if any(term in concept_text for term in ['education', 'student', 'teacher', 'learning']):
            personas.extend([
                "University Student",
                "High School Student",
                "Adult Learner",
                "Experienced Teacher",
                "New Educator",
                "Education Administrator", 
                "Parent/Guardian",
                "Online Learner"
            ])
        
        # Business personas
        if any(term in concept_text for term in ['business', 'company', 'management', 'finance']):
            personas.extend([
                "Business Owner",
                "C-Level Executive",
                "Middle Manager",
                "Entry-Level Employee",
                "Entrepreneur",
                "Consultant",
                "Sales Representative",
                "Financial Analyst"
            ])
        
        return personas
    
    def _get_demographic_variations(self, core_concepts: List[str]) -> List[str]:
        """
        Generate demographic persona variations
        """
        return [
            "Young Adult (18-25)",
            "Early Career Professional (26-35)",
            "Experienced Professional (36-50)", 
            "Senior Expert (51+)",
            "Working Parent",
            "Recent Graduate",
            "Career Changer",
            "Remote Worker",
            "Urban Professional",
            "Rural Community Member",
            "Small Business Owner",
            "Corporate Employee"
        ]
    
    def _get_fallback_suggestions(self) -> List[str]:
        """
        Fallback persona suggestions covering common archetypes
        """
        return [
            "Expert User",
            "Novice User",
            "Intermediate User", 
            "Business Professional",
            "Individual Consumer",
            "Technical Specialist",
            "General User",
            "Decision Maker",
            "End User",
            "Administrator",
            "Researcher",
            "Student",
            "Senior Professional",
            "Young Professional",
            "Small Business Owner"
        ]