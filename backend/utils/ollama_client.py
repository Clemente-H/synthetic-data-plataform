#!/usr/bin/env python3
"""
Ollama Client - Configurable client for different models
"""

import httpx
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import asyncio

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "models.yaml"
        
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.base_url = self.config["ollama_url"]
        self.default_model = self.config["default_model"]
        self.models = self.config["models"]
        self.fallback_models = self.config["fallback_models"]
        
        # HTTP client with timeout
        self.client = httpx.AsyncClient(timeout=120.0)
        
        logger.info(f"OllamaClient initialized with {self.default_model}")
    
    async def check_health(self) -> bool:
        """Check if Ollama is running and models are available"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models_data = response.json()
                available_models = [m["name"] for m in models_data.get("models", [])]
                
                # Check if default model is available
                model_available = any(self.default_model in name for name in available_models)
                
                logger.info(f"Ollama health: {'✅' if model_available else '❌'} {self.default_model}")
                return model_available
            return False
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
    
    async def generate(self, prompt: str, system_prompt: str = "", 
                      task_type: str = "default", max_retries: int = 2) -> str:
        """
        Generate response using appropriate model for task type
        """
        # Select model based on task type
        if task_type in self.models:
            model_config = self.models[task_type]
            model = model_config["model"]
            temperature = model_config["temperature"]
            max_tokens = model_config["max_tokens"]
        else:
            model = self.default_model
            temperature = self.config["temperature"]
            max_tokens = self.config["max_tokens"]
        
        models_to_try = [model] + self.fallback_models
        
        for attempt, current_model in enumerate(models_to_try):
            if attempt > max_retries:
                break
                
            try:
                logger.info(f"Generating with {current_model} (attempt {attempt + 1})")
                
                payload = {
                    "model": current_model,
                    "prompt": prompt,
                    "system": system_prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                }
                
                response = await self.client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    generated_text = result.get("response", "").strip()
                    
                    if generated_text:
                        logger.info(f"✅ Generated {len(generated_text)} chars with {current_model}")
                        return generated_text
                    else:
                        logger.warning(f"Empty response from {current_model}")
                else:
                    logger.warning(f"HTTP {response.status_code} from {current_model}")
                    
            except Exception as e:
                logger.error(f"Error with {current_model}: {e}")
                if attempt < len(models_to_try) - 1:
                    logger.info(f"Trying fallback model...")
                    await asyncio.sleep(1)  # Brief pause before retry
        
        raise Exception(f"All models failed after {max_retries + 1} attempts")
    
    def extract_json_from_response(self, response: str) -> Optional[str]:
        """
        Extract JSON content from LLM response
        """
        # Look for JSON blocks
        import re
        
        # Try to find JSON between ```json and ```
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            return json_match.group(1).strip()
        
        # Try to find JSON between ``` and ```
        json_match = re.search(r'```\s*([\[\{].*?[\]\}])\s*```', response, re.DOTALL)
        if json_match:
            return json_match.group(1).strip()
        
        # Try to find JSON directly (starts with [ or {)
        json_match = re.search(r'([\[\{].*?[\]\}])', response, re.DOTALL)
        if json_match:
            return json_match.group(1).strip()
        
        return None
    
    def parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON from LLM response
        """
        json_text = self.extract_json_from_response(response)
        if json_text:
            try:
                return json.loads(json_text)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode error: {e}")
                # Try to fix common JSON issues
                fixed_json = json_text.replace("'", '"').replace('True', 'true').replace('False', 'false')
                try:
                    return json.loads(fixed_json)
                except json.JSONDecodeError:
                    logger.error("Could not parse JSON even after fixes")
        
        return None
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

# Global client instance
ollama_client = OllamaClient()