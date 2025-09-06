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
        Generate suggestions using LLM - no fallbacks, proper error handling
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
            
            logger.info(f"{self.__class__.__name__} received response length: {len(response)}")
            logger.debug(f"{self.__class__.__name__} raw response: {response[:300]}...")
            
            # Parse JSON response - if it fails, raise error
            suggestions = self._extract_suggestions_from_response(response, max_suggestions)
            
            if not suggestions:
                logger.error(f"{self.__class__.__name__} - No suggestions extracted from response")
                raise Exception(f"LLM failed to generate valid JSON for {self.__class__.__name__}")
            
            logger.info(f"{self.__class__.__name__} generated {len(suggestions)} suggestions from LLM")
            return suggestions
            
        except Exception as e:
            logger.error(f"{self.__class__.__name__} error: {str(e)}")
            raise e
    
    def _extract_suggestions_from_response(self, response: str, max_suggestions: int = 15) -> List[str]:
        """
        Extract suggestions from LLM JSON response - strict parsing only
        """
        # Parse JSON response
        json_data = self.client.parse_json_response(response)
        
        if not json_data:
            logger.error(f"No valid JSON found in response: {response[:200]}...")
            return []
        
        suggestions = []
        
        # Expect array of strings: ["item1", "item2", "item3"]
        if isinstance(json_data, list):
            for item in json_data:
                if isinstance(item, str) and item.strip():
                    suggestions.append(item.strip())
                elif isinstance(item, dict):
                    # For dict format, extract the main context value
                    context_key = f"{self.agent_type}_context"
                    if context_key in item and item[context_key]:
                        suggestions.append(str(item[context_key]).strip())
        
        # Or expect dict with agent-specific key: {"cultural": ["item1", "item2"]}
        elif isinstance(json_data, dict):
            if self.agent_type in json_data and isinstance(json_data[self.agent_type], list):
                suggestions = [str(item).strip() for item in json_data[self.agent_type] if str(item).strip()]
        
        # Filter valid suggestions
        valid_suggestions = [s for s in suggestions if s and len(s) > 2]
        
        if valid_suggestions:
            logger.info(f"Extracted {len(valid_suggestions)} valid suggestions from LLM JSON")
            return valid_suggestions[:max_suggestions]
        
        logger.error(f"No valid suggestions found in JSON: {json_data}")
        return []
    
    
    def validate_suggestions(self, suggestions: List[str]) -> List[str]:
        """
        Validate and filter suggestions
        """
        validated = []
        for suggestion in suggestions:
            if isinstance(suggestion, str) and 2 < len(suggestion.strip()) < 100:
                validated.append(suggestion.strip())
        
        return list(set(validated))  # Remove duplicates