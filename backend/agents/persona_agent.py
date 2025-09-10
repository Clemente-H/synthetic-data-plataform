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
        Generate persona contexts using LLM only - no keyword matching
        """
        logger.info(f"Processing persona contexts for concepts: {core_concepts}")
        
        # Generate persona suggestions using LLM only
        suggestions = await self._generate_suggestions(
            core_concepts, 
            additional_context,
            max_suggestions=15
        )
        
        # Validate and return
        validated = self.validate_suggestions(suggestions)
        return validated
    
