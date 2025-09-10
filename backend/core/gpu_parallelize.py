#!/usr/bin/env python3
"""
GPU Parallelization for Synthetic Data Generation
Distributes workload across multiple H100 GPUs
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor
import math

from config.gpu_config import (
    MAX_PARALLEL_GPUS, 
    BATCH_SIZE_PER_GPU,
    GENERATION_TIMEOUT,
    PARALLEL_STAGES
)
from utils.ollama_client import ollama_client
from utils.prompt_loader import prompt_loader

logger = logging.getLogger(__name__)

class GPUParallelizer:
    """Distributes generation tasks across multiple GPUs"""
    
    def __init__(self):
        self.active_gpus = MAX_PARALLEL_GPUS
        self.batch_size = BATCH_SIZE_PER_GPU
        self.semaphore = asyncio.Semaphore(self.active_gpus)
        
        logger.info(f"🚀 GPU Parallelizer initialized: {self.active_gpus} GPUs, batch size {self.batch_size}")
    
    async def parallel_characterization(self, agents: Dict, concept_names: List[str]) -> Dict[str, List[str]]:
        """Run characterization agents in parallel"""
        logger.info(f"🤖 Running {len(agents)} characterization agents in parallel")
        
        tasks = []
        for agent_name, agent in agents.items():
            task = self._run_agent_with_semaphore(agent_name, agent, concept_names)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        characterization_results = {}
        for i, (agent_name, result) in enumerate(zip(agents.keys(), results)):
            if isinstance(result, Exception):
                logger.warning(f"⚠️ {agent_name} agent failed: {result}")
                characterization_results[agent_name] = []
            else:
                characterization_results[agent_name] = result
                logger.info(f"✅ {agent_name}: {len(result)} suggestions")
        
        return characterization_results
    
    async def _run_agent_with_semaphore(self, agent_name: str, agent, concept_names: List[str]) -> List[str]:
        """Run single agent with GPU semaphore"""
        async with self.semaphore:
            logger.info(f"🎯 Processing {agent_name} agent on available GPU")
            try:
                return await agent.process(concept_names, {})
            except Exception as e:
                logger.error(f"❌ {agent_name} agent failed: {e}")
                raise
    
    async def parallel_generation(self, 
                                sample_combinations: List[Dict],
                                generation_config: Dict[str, Any],
                                websocket_task_id: Optional[str] = None,
                                progress_callback: Optional[Callable] = None) -> List[Dict[str, Any]]:
        """Distribute generation across GPUs in batches"""
        
        total_combinations = len(sample_combinations)
        logger.info(f"⚡ Starting parallel generation: {total_combinations} combinations across {self.active_gpus} GPUs")
        
        # Split combinations into GPU batches
        batches = self._create_gpu_batches(sample_combinations)
        logger.info(f"📊 Created {len(batches)} batches, max {self.batch_size} combinations per batch")
        
        all_generated_samples = []
        completed_combinations = 0
        
        # Process batches in parallel
        for batch_idx, batch in enumerate(batches):
            logger.info(f"🎯 Processing batch {batch_idx + 1}/{len(batches)} ({len(batch)} combinations)")
            
            # Create parallel tasks for this batch
            batch_tasks = []
            for combo in batch:
                task = self._generate_combination_with_semaphore(
                    combo, 
                    generation_config,
                    completed_combinations + len(batch_tasks),
                    total_combinations,
                    websocket_task_id
                )
                batch_tasks.append(task)
            
            # Execute batch in parallel
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Process batch results
            for i, result in enumerate(batch_results):
                completed_combinations += 1
                
                if isinstance(result, Exception):
                    combo_id = batch[i].get('combination_id', 'unknown')
                    logger.warning(f"⚠️ Generation failed for combination {combo_id}: {result}")
                    continue
                
                if result:  # Successfully generated samples
                    all_generated_samples.extend(result)
                
                # Progress callback
                if progress_callback:
                    await progress_callback({
                        "completed": completed_combinations,
                        "total": total_combinations,
                        "samples_generated": len(all_generated_samples),
                        "current_batch": batch_idx + 1,
                        "total_batches": len(batches)
                    })
        
        logger.info(f"✅ Parallel generation complete: {len(all_generated_samples)} samples from {completed_combinations} combinations")
        return all_generated_samples
    
    async def _generate_combination_with_semaphore(self,
                                                 combo: Dict[str, Any],
                                                 generation_config: Dict[str, Any], 
                                                 combo_index: int,
                                                 total_combinations: int,
                                                 websocket_task_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Generate samples for single combination with GPU semaphore"""
        
        async with self.semaphore:
            combo_id = combo.get('combination_id', 'unknown')
            logger.info(f"🤖 Generating combination {combo_index + 1}/{total_combinations} (ID: {combo_id})")
            
            try:
                # Get generation template
                template_data = prompt_loader.get_generation_template(
                    generation_config["format_type"],
                    combo,
                    combo.get("complexity_level", 1),
                    generation_config.get("samples_per_combination", 2)
                )
                
                # Generate with timeout
                response = await asyncio.wait_for(
                    ollama_client.generate(
                        prompt=template_data['user'],
                        system_prompt=template_data['system'],
                        task_type='generation'
                    ),
                    timeout=GENERATION_TIMEOUT
                )
                
                # Save debug file
                debug_filename = f"debug_generation_parallel_{combo_id}.txt"
                try:
                    with open(debug_filename, 'w', encoding='utf-8') as f:
                        f.write(f"=== COMBINATION {combo_index + 1}/{total_combinations} ===\n")
                        f.write(f"ID: {combo_id}\n\n")
                        f.write(f"=== PROMPT ===\n{template_data['user']}\n\n")
                        f.write(f"=== RESPONSE ===\n{response}")
                except Exception as save_error:
                    logger.warning(f"Failed to save debug file: {save_error}")
                
                # Parse response
                samples = self._parse_generation_response(response, combo)
                logger.info(f"✅ Generated {len(samples)} samples for {combo_id}")
                
                return samples
                
            except asyncio.TimeoutError:
                logger.warning(f"⏱️ Generation timeout for combination {combo_id}")
                return []
            except Exception as e:
                logger.error(f"❌ Generation error for combination {combo_id}: {e}")
                return []
    
    def _create_gpu_batches(self, combinations: List[Dict]) -> List[List[Dict]]:
        """Split combinations into GPU-sized batches"""
        batches = []
        for i in range(0, len(combinations), self.batch_size):
            batch = combinations[i:i + self.batch_size]
            batches.append(batch)
        return batches
    
    def _parse_generation_response(self, response: str, combination: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse generated samples from LLM response"""
        json_data = ollama_client.parse_json_response(response)
        
        if json_data and isinstance(json_data, list):
            samples = []
            for item in json_data:
                if isinstance(item, dict):
                    item.update({
                        "combination_id": combination.get("combination_id"),
                        "pipeline_generated": True,
                        "parallel_generated": True
                    })
                    samples.append(item)
            return samples
        
        # Fallback
        return [{
            "content": response.strip(),
            "combination_id": combination.get("combination_id"),
            "pipeline_generated": True,
            "parallel_generated": True,
            "parsed_as": "fallback"
        }]
    
    def update_gpu_count(self, new_count: int):
        """Dynamically update GPU count (1-8)"""
        if 1 <= new_count <= 8:
            self.active_gpus = new_count
            self.semaphore = asyncio.Semaphore(new_count)
            logger.info(f"🔄 Updated GPU count to {new_count}")
        else:
            logger.warning(f"⚠️ Invalid GPU count: {new_count}. Must be 1-8.")