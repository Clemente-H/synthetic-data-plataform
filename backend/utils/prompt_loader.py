#!/usr/bin/env python3
"""
Prompt Loader - Load and format prompts from YAML files
"""

import yaml
import os
from typing import Dict, Any, List
from pathlib import Path

class PromptLoader:
    def __init__(self, prompts_dir: str = None):
        if prompts_dir is None:
            # Go up from backend/utils to root, then to prompts
            current_dir = Path(__file__).parent.parent.parent
            self.prompts_dir = current_dir / "prompts"
        else:
            self.prompts_dir = Path(prompts_dir)
        
        self._cache = {}
    
    def load_prompt(self, category: str, prompt_name: str) -> Dict[str, Any]:
        """
        Load a prompt from prompts/{category}/{prompt_name}.yaml
        """
        cache_key = f"{category}/{prompt_name}"
        
        if cache_key not in self._cache:
            prompt_path = self.prompts_dir / category / f"{prompt_name}.yaml"
            
            if not prompt_path.exists():
                raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
            
            with open(prompt_path, 'r', encoding='utf-8') as f:
                self._cache[cache_key] = yaml.safe_load(f)
        
        return self._cache[cache_key]
    
    def format_prompt(self, category: str, prompt_name: str, **kwargs) -> Dict[str, str]:
        """
        Load and format a prompt with given variables
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            prompt_data = self.load_prompt(category, prompt_name)
            logger.info(f"📄 Loaded prompt: {category}/{prompt_name}")
            
            # Format both system and user prompts
            formatted = {}
            
            if 'system_prompt' in prompt_data:
                logger.info(f"🔧 Formatting system prompt with {len(kwargs)} variables")
                formatted['system'] = prompt_data['system_prompt'].format(**kwargs)
                logger.info(f"✅ System prompt formatted successfully")
            
            if 'user_prompt' in prompt_data:
                logger.info(f"🔧 Formatting user prompt with variables: {list(kwargs.keys())}")
                formatted['user'] = prompt_data['user_prompt'].format(**kwargs)
                logger.info(f"✅ User prompt formatted successfully, length: {len(formatted['user'])}")
            
            # Include validation and fallback data
            if 'validation' in prompt_data:
                formatted['validation'] = prompt_data['validation']
            
            if 'fallback_suggestions' in prompt_data:
                formatted['fallback'] = prompt_data['fallback_suggestions']
            
            return formatted
            
        except Exception as e:
            logger.error(f"❌ Error in format_prompt({category}/{prompt_name}): {e}")
            logger.error(f"Variables passed: {kwargs}")
            raise e
    
    def get_generation_template(self, format_type: str, concepts: Dict[str, List[str]], 
                              complexity_level: int = 1, samples_per_combination: int = 5) -> Dict[str, str]:
        """
        Get a formatted generation template
        """
        # Convert concept lists to comma-separated strings for prompt
        concept_strings = {}
        for key, value_list in concepts.items():
            if isinstance(value_list, list):
                concept_strings[key] = ", ".join(value_list) if value_list else "General"
            else:
                concept_strings[key] = str(value_list)
        
        return self.format_prompt(
            'generation', 
            f"{format_type}_format",
            core_concepts=concept_strings.get('core_concepts', 'General'),
            geographic_context=concept_strings.get('geographic', 'Global'),
            cultural_context=concept_strings.get('cultural', 'General'),
            linguistic_context=concept_strings.get('linguistic', 'Standard'),
            persona_context=concept_strings.get('persona', 'General User'),
            domain_context=concept_strings.get('domain', 'General'),
            complexity_level=complexity_level,
            samples_per_combination=samples_per_combination
        )
    
    def get_characterization_prompt(self, agent_type: str, core_concepts: List[str], 
                                  additional_context: Dict[str, List[str]] = None) -> Dict[str, str]:
        """
        Get a formatted characterization prompt for agents
        """
        additional_context = additional_context or {}
        
        return self.format_prompt(
            'characterization',
            agent_type,
            core_concepts=", ".join(core_concepts),
            geographic_context=", ".join(additional_context.get('geographic', [])),
            **{k: ", ".join(v) if isinstance(v, list) else v 
               for k, v in additional_context.items()}
        )

# Global instance
prompt_loader = PromptLoader()