#!/usr/bin/env python3
"""
Concept Extractor Agent - Step 2: Extract 20-50 core concepts from user input
"""

from typing import List, Dict, Any
import logging
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class ConceptExtractor(BaseAgent):
    """
    Extracts 20-50 core concepts from user input text
    This is step 2 in the pipeline
    """
    
    def __init__(self):
        super().__init__("concept_extraction")
        self.target_concepts = 30  # Aim for ~30 concepts
    
    async def extract_from_text(self, input_text: str, 
                               max_concepts: int = 50) -> List[Dict[str, Any]]:
        """
        Extract concepts from user input text
        
        Args:
            input_text: User's input text/document
            max_concepts: Maximum number of concepts to extract
            
        Returns:
            List of concept dictionaries with name, relevance, category
        """
        try:
            logger.info(f"Extracting concepts from {len(input_text)} characters of text")
            
            # Create extraction prompt
            system_prompt = """
            You are an expert at extracting key concepts from text. Your role is to identify 
            20-50 core concepts, terms, entities, and ideas that are central to the input text.
            
            Focus on:
            - Main topics and themes
            - Important entities (people, places, organizations)
            - Technical terms and domain-specific concepts
            - Key processes or procedures
            - Important relationships or connections
            
            Return a JSON array of concepts with relevance scores.
            """
            
            user_prompt = f"""
            Extract 20-50 key concepts from this text. For each concept, provide:
            - name: The concept name
            - relevance: Score 1-10 (10 = most relevant)
            - category: Type (entity, process, domain_term, theme, etc.)
            - description: Brief explanation
            
            Text to analyze:
            ```
            {input_text[:3000]}  # Limit text to avoid token limits
            ```
            
            Format as JSON array:
            ```json
            [
              {{
                "name": "Concept Name",
                "relevance": 9,
                "category": "entity",
                "description": "Brief explanation"
              }}
            ]
            ```
            """
            
            # Generate concepts
            response = await self.client.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                task_type='concept_extraction'
            )
            
            # Parse response
            concepts = self._parse_concepts_response(response, max_concepts)
            
            if not concepts:
                # Fallback extraction
                concepts = self._extract_concepts_fallback(input_text, max_concepts)
            
            logger.info(f"✅ Extracted {len(concepts)} concepts")
            return concepts
            
        except Exception as e:
            logger.error(f"Concept extraction failed: {e}")
            return self._extract_concepts_fallback(input_text, max_concepts)
    
    def _parse_concepts_response(self, response: str, max_concepts: int) -> List[Dict[str, Any]]:
        """
        Parse concepts from LLM response
        """
        json_data = self.client.parse_json_response(response)
        
        if json_data and isinstance(json_data, list):
            concepts = []
            
            for item in json_data:
                if isinstance(item, dict) and 'name' in item:
                    concept = {
                        'name': str(item.get('name', '')).strip(),
                        'relevance': int(item.get('relevance', 5)),
                        'category': str(item.get('category', 'general')).strip(),
                        'description': str(item.get('description', '')).strip()
                    }
                    
                    if concept['name'] and len(concept['name']) > 1:
                        concepts.append(concept)
            
            # Sort by relevance and limit
            concepts.sort(key=lambda x: x['relevance'], reverse=True)
            return concepts[:max_concepts]
        
        return []
    
    def _extract_concepts_fallback(self, input_text: str, max_concepts: int) -> List[Dict[str, Any]]:
        """
        Fallback concept extraction using simple text analysis
        """
        import re
        from collections import Counter
        
        logger.warning("Using fallback concept extraction")
        
        # Simple keyword extraction
        words = re.findall(r'\b[A-Za-z]{3,}\b', input_text.lower())
        
        # Filter common words (simple stopwords)
        stopwords = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'this', 'that', 'are', 'was', 'were', 'been', 'have', 'has', 'had', 'will', 'would', 'could', 'should'}
        
        filtered_words = [w for w in words if w not in stopwords and len(w) > 3]
        
        # Get most common words
        word_counts = Counter(filtered_words)
        common_words = word_counts.most_common(max_concepts)
        
        concepts = []
        for word, count in common_words:
            concepts.append({
                'name': word.title(),
                'relevance': min(10, count + 3),  # Simple relevance based on frequency
                'category': 'extracted_term',
                'description': f'Extracted term (appeared {count} times)'
            })
        
        return concepts
    
    async def process(self, core_concepts: List[str], 
                     additional_context: Dict[str, List[str]] = None) -> List[str]:
        """
        BaseAgent interface - not used for concept extraction
        """
        return core_concepts
    
    def _get_fallback_suggestions(self) -> List[str]:
        """
        BaseAgent interface - return generic concepts
        """
        return [
            "General Topic",
            "Main Theme", 
            "Key Process",
            "Important Entity",
            "Domain Concept"
        ]