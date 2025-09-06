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
        Generate geographic contexts using LLM only - no keyword matching
        """
        logger.info(f"Processing geographic contexts for concepts: {core_concepts}")
        
        # Generate geographic suggestions using LLM only
        suggestions = await self._generate_suggestions(
            core_concepts, 
            additional_context,
            max_suggestions=15
        )
        
        # Validate and return
        validated = self.validate_suggestions(suggestions)
        return validated
    
