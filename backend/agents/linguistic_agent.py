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
        Generate linguistic contexts using LLM only - no keyword matching
        """
        logger.info(f"Processing linguistic contexts for concepts: {core_concepts}")
        
        # Generate linguistic suggestions using LLM only
        suggestions = await self._generate_suggestions(
            core_concepts, 
            additional_context,
            max_suggestions=15
        )
        
        # Validate and return
        validated = self.validate_suggestions(suggestions)
        return validated
    
