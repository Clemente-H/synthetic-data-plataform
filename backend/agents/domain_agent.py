#!/usr/bin/env python3
"""
Domain Agent - Identifies technical concepts, terminology, and specialized knowledge
"""

from typing import List, Dict, Any
import logging
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class DomainAgent(BaseAgent):
    """
    Specialized agent for domain context characterization
    Identifies technical concepts, industry-specific terminology, 
    edge cases, and specialized knowledge requirements
    """
    
    def __init__(self):
        super().__init__("domain")
    
    async def process(self, core_concepts: List[str], 
                     additional_context: Dict[str, List[str]] = None) -> List[str]:
        """
        Generate domain contexts using LLM only - no keyword matching
        """
        logger.info(f"Processing domain contexts for concepts: {core_concepts}")
        
        # Generate domain suggestions using LLM only
        suggestions = await self._generate_suggestions(
            core_concepts, 
            additional_context,
            max_suggestions=15
        )
        
        # Validate and return
        validated = self.validate_suggestions(suggestions)
        return validated
    
