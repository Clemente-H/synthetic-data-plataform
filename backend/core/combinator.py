#!/usr/bin/env python3
"""
Combinatorial Generator - Create massive concept combinations for 50K+ samples
"""

import itertools
from typing import Dict, List, Any, Iterator, Tuple
import logging

logger = logging.getLogger(__name__)

class ConceptCombinator:
    """
    Generates combinations of concepts across multiple dimensions
    to achieve massive scale (50K+ samples) through combinatorial explosion
    """
    
    def __init__(self, max_combinations: int = 100000):
        self.max_combinations = max_combinations
    
    def generate_combinations(self, concept_dimensions: Dict[str, List[str]], 
                            complexity_levels: List[int] = [1, 2, 3]) -> Iterator[Dict[str, Any]]:
        """
        Generate all possible combinations of concepts across dimensions
        
        Args:
            concept_dimensions: Dict with lists of concepts per dimension
            complexity_levels: List of complexity levels to iterate through
            
        Yields:
            Dict containing one combination of concepts + complexity level
        """
        
        # Filter out empty dimensions
        active_dimensions = {k: v for k, v in concept_dimensions.items() if v}
        
        if not active_dimensions:
            logger.warning("No active concept dimensions provided")
            return
        
        logger.info(f"Generating combinations from {len(active_dimensions)} dimensions:")
        for dim, concepts in active_dimensions.items():
            logger.info(f"  {dim}: {len(concepts)} concepts")
        
        # Calculate total possible combinations
        total_concept_combinations = 1
        for concepts in active_dimensions.values():
            total_concept_combinations *= len(concepts)
        
        total_combinations = total_concept_combinations * len(complexity_levels)
        
        logger.info(f"Total possible combinations: {total_combinations:,}")
        
        if total_combinations > self.max_combinations:
            logger.warning(f"Limiting to {self.max_combinations:,} combinations")
        
        # Generate combinations using itertools.product
        dimension_names = list(active_dimensions.keys())
        concept_lists = [active_dimensions[dim] for dim in dimension_names]
        
        count = 0
        for complexity in complexity_levels:
            for concept_combo in itertools.product(*concept_lists):
                if count >= self.max_combinations:
                    logger.info(f"Reached maximum combinations limit: {self.max_combinations:,}")
                    return
                
                # Create combination dict
                combination = {
                    'combination_id': f"combo_{count:06d}",
                    'complexity_level': complexity
                }
                
                # Add concepts for each dimension
                for i, dim_name in enumerate(dimension_names):
                    combination[dim_name] = concept_combo[i]
                
                yield combination
                count += 1
        
        logger.info(f"Generated {count:,} total combinations")
    
    def generate_batched_combinations(self, concept_dimensions: Dict[str, List[str]], 
                                    batch_size: int = 100, 
                                    complexity_levels: List[int] = [1, 2, 3]) -> Iterator[List[Dict[str, Any]]]:
        """
        Generate combinations in batches for memory efficiency
        """
        batch = []
        
        for combination in self.generate_combinations(concept_dimensions, complexity_levels):
            batch.append(combination)
            
            if len(batch) >= batch_size:
                yield batch
                batch = []
        
        # Yield remaining batch
        if batch:
            yield batch
    
    def estimate_total_samples(self, concept_dimensions: Dict[str, List[str]], 
                             samples_per_combination: int,
                             complexity_levels: List[int] = [1, 2, 3]) -> Tuple[int, Dict[str, int]]:
        """
        Estimate total samples that would be generated
        """
        active_dimensions = {k: v for k, v in concept_dimensions.items() if v}
        
        if not active_dimensions:
            return 0, {}
        
        # Calculate combinations
        total_concept_combinations = 1
        for concepts in active_dimensions.values():
            total_concept_combinations *= len(concepts)
        
        total_combinations = min(
            total_concept_combinations * len(complexity_levels),
            self.max_combinations
        )
        
        total_samples = total_combinations * samples_per_combination
        
        stats = {
            'total_combinations': total_combinations,
            'samples_per_combination': samples_per_combination,
            'total_samples': total_samples,
            'dimensions_used': len(active_dimensions),
            'complexity_levels': len(complexity_levels)
        }
        
        return total_samples, stats
    
    def preview_combinations(self, concept_dimensions: Dict[str, List[str]], 
                           limit: int = 10) -> List[Dict[str, Any]]:
        """
        Preview first few combinations for validation
        """
        combinations = []
        
        for i, combo in enumerate(self.generate_combinations(concept_dimensions)):
            if i >= limit:
                break
            combinations.append(combo)
        
        return combinations

# Example usage
if __name__ == "__main__":
    # Test with sample data
    sample_dimensions = {
        'core_concepts': ['AI', 'Healthcare', 'Education'],
        'geographic': ['USA', 'Europe', 'Asia'],
        'cultural': ['Traditional', 'Modern', 'Mixed'],
        'persona': ['Expert', 'Beginner', 'Intermediate'],
        'domain': ['Technical', 'General', 'Academic']
    }
    
    combinator = ConceptCombinator()
    
    # Estimate
    total, stats = combinator.estimate_total_samples(sample_dimensions, samples_per_combination=5)
    print(f"Estimated total samples: {total:,}")
    print(f"Stats: {stats}")
    
    # Preview
    preview = combinator.preview_combinations(sample_dimensions, limit=5)
    for combo in preview:
        print(f"Combination: {combo}")