#!/usr/bin/env python3
"""
Base Agent - Abstract base class for specialized agents
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging
from utils.ollama_client import ollama_client
from utils.prompt_loader import prompt_loader

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    Abstract base class for all specialized agents
    """
    
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.client = ollama_client
        self.prompt_loader = prompt_loader
        logger.info(f"Initialized {self.__class__.__name__}")
    
    @abstractmethod
    async def process(self, core_concepts: List[str], 
                     additional_context: Dict[str, List[str]] = None) -> List[str]:
        """
        Process concepts and return suggestions for this agent's domain
        
        Args:
            core_concepts: List of base concepts extracted from user input
            additional_context: Context from other agents (e.g., geographic for cultural)
        
        Returns:
            List of suggestions for this agent's specialization
        """
        pass
    
    async def _generate_suggestions(self, core_concepts: List[str], 
                                  additional_context: Dict[str, List[str]] = None,
                                  max_suggestions: int = 15) -> List[str]:
        """
        Common method to generate suggestions using prompts
        """
        try:
            # Get formatted prompt for this agent
            prompt_data = self.prompt_loader.get_characterization_prompt(
                self.agent_type, 
                core_concepts, 
                additional_context or {}
            )
            
            # Generate with appropriate model
            response = await self.client.generate(
                prompt=prompt_data['user'],
                system_prompt=prompt_data['system'],
                task_type='characterization'
            )
            
            # Try to parse JSON response
            suggestions = self._extract_suggestions_from_response(response, max_suggestions)
            
            if not suggestions:
                # Use fallback suggestions
                suggestions = self._get_fallback_suggestions()
            
            logger.info(f"{self.__class__.__name__} generated {len(suggestions)} suggestions")
            return suggestions
            
        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}: {e}")
            return self._get_fallback_suggestions()
    
    def _extract_suggestions_from_response(self, response: str, max_suggestions: int = 15) -> List[str]:
        """
        Extract suggestions from LLM response
        """
        # Try to parse as JSON first
        json_data = self.client.parse_json_response(response)
        
        if json_data:
            suggestions = []
            
            # Handle different JSON formats
            if isinstance(json_data, list):
                # Direct list of suggestions
                for item in json_data:
                    if isinstance(item, str):
                        suggestions.append(item.strip())
                    elif isinstance(item, dict) and 'cultural_context' in item:
                        suggestions.append(item['cultural_context'].strip())
                    elif isinstance(item, dict) and any(key in item for key in ['suggestion', 'context', 'name']):
                        # Extract from various possible keys
                        for key in ['suggestion', 'context', 'name', 'geographic_context']:
                            if key in item and item[key]:
                                suggestions.append(str(item[key]).strip())
                                break
            
            # Filter and limit suggestions
            suggestions = [s for s in suggestions if s and len(s.strip()) > 2]
            return suggestions[:max_suggestions]
        
        # If JSON parsing fails, try to extract from text
        return self._extract_from_text(response, max_suggestions)
    
    def _extract_from_text(self, response: str, max_suggestions: int = 15) -> List[str]:
        """
        Extract suggestions from plain text response
        """
        lines = response.split('\n')
        suggestions = []
        
        for line in lines:
            line = line.strip()
            # Look for bullet points, numbers, or clean text
            if line and (line.startswith('-') or line.startswith('*') or 
                        line.startswith(tuple('123456789')) or 
                        (len(line) > 3 and len(line) < 100)):
                # Clean up the line
                cleaned = line.lstrip('-*0123456789. ').strip()
                if cleaned and len(cleaned) > 2:
                    suggestions.append(cleaned)
        
        return suggestions[:max_suggestions]
    
    @abstractmethod
    def _get_fallback_suggestions(self) -> List[str]:
        """
        Return fallback suggestions if AI generation fails
        """
        pass
    
    def validate_suggestions(self, suggestions: List[str]) -> List[str]:
        """
        Validate and filter suggestions
        """
        validated = []
        for suggestion in suggestions:
            if isinstance(suggestion, str) and 2 < len(suggestion.strip()) < 100:
                validated.append(suggestion.strip())
        
        return list(set(validated))  # Remove duplicates