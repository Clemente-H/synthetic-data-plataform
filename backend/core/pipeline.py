#!/usr/bin/env python3
"""
Pipeline Orchestrator - Coordinates all steps (1-8) of the synthetic data generation process
"""

from typing import Dict, List, Any, Optional, Callable
import logging
import asyncio
from datetime import datetime
from enum import Enum

from agents.concept_extractor import ConceptExtractor
from agents.geographic_agent import GeographicAgent
from agents.cultural_agent import CulturalAgent
from agents.linguistic_agent import LinguisticAgent
from agents.persona_agent import PersonaAgent
from agents.domain_agent import DomainAgent
from core.combinator import ConceptCombinator
from utils.ollama_client import ollama_client
from utils.prompt_loader import prompt_loader

# Import WebSocket helpers - handle gracefully if not available
try:
    from api.websocket import send_pipeline_update, send_pipeline_error, send_pipeline_complete
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    async def send_pipeline_update(*args, **kwargs): pass
    async def send_pipeline_error(*args, **kwargs): pass
    async def send_pipeline_complete(*args, **kwargs): pass

logger = logging.getLogger(__name__)

class PipelineStage(Enum):
    INPUT_PROCESSING = "input_processing"
    CONCEPT_EXTRACTION = "concept_extraction"
    CHARACTERIZATION = "characterization"
    HUMAN_VALIDATION = "human_validation"
    FORMAT_SELECTION = "format_selection"
    GENERATION = "generation"
    QUALITY_ASSURANCE = "quality_assurance"
    EXPORT = "export"

class PipelineOrchestrator:
    """
    Orchestrates the complete 8-step pipeline for synthetic data generation
    """
    
    def __init__(self):
        self.concept_extractor = ConceptExtractor()
        self.agents = {
            'geographic': GeographicAgent(),
            'cultural': CulturalAgent(),
            'linguistic': LinguisticAgent(),
            'persona': PersonaAgent(),
            'domain': DomainAgent()
        }
        self.combinator = ConceptCombinator(max_combinations=50000)
        
        # Pipeline state tracking
        self.current_stage = None
        self.pipeline_state = {}
        
        logger.info("🎭 Pipeline Orchestrator initialized with 5 specialized agents")
    
    async def run_full_pipeline(self, 
                               input_text: str,
                               format_type: str = "qa",
                               samples_per_combination: int = 3,
                               max_total_samples: int = 10000,
                               progress_callback: Optional[Callable] = None,
                               websocket_task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute the complete 8-step pipeline
        
        Steps:
        1. Input Processing
        2. Concept Extraction (20-50 concepts)
        3. Multi-Dimensional Characterization (5 agents)
        4. Human Validation (simulated for automated run)
        5. Format Selection
        6. Combinatorial Generation
        7. Quality Assurance
        8. HuggingFace Export
        """
        
        start_time = datetime.now()
        pipeline_id = f"pipeline_{int(start_time.timestamp())}"
        
        try:
            logger.info(f"🚀 Starting full pipeline execution (ID: {pipeline_id})")
            
            # Initialize pipeline state
            self.pipeline_state = {
                "pipeline_id": pipeline_id,
                "start_time": start_time.isoformat(),
                "current_stage": None,
                "stages_completed": [],
                "results": {},
                "metadata": {}
            }
            
            # Step 1: Input Processing
            await self._update_stage(PipelineStage.INPUT_PROCESSING, progress_callback, websocket_task_id)
            processed_input = await self._step_1_input_processing(input_text)
            
            # Step 2: Concept Extraction
            await self._update_stage(PipelineStage.CONCEPT_EXTRACTION, progress_callback, websocket_task_id)
            concepts = await self._step_2_concept_extraction(processed_input["text"])
            
            # Step 3: Multi-Dimensional Characterization
            await self._update_stage(PipelineStage.CHARACTERIZATION, progress_callback, websocket_task_id)
            characterization = await self._step_3_characterization(concepts)
            
            # Step 4: Human Validation (simulated)
            await self._update_stage(PipelineStage.HUMAN_VALIDATION, progress_callback, websocket_task_id)
            validated_concepts = await self._step_4_human_validation(characterization)
            
            # Step 5: Format Selection
            await self._update_stage(PipelineStage.FORMAT_SELECTION, progress_callback, websocket_task_id)
            generation_config = await self._step_5_format_selection(format_type, samples_per_combination)
            
            # Step 6: Combinatorial Generation
            await self._update_stage(PipelineStage.GENERATION, progress_callback, websocket_task_id)
            generated_data = await self._step_6_generation(
                validated_concepts, 
                generation_config,
                max_total_samples,
                websocket_task_id
            )
            
            # Step 7: Quality Assurance
            await self._update_stage(PipelineStage.QUALITY_ASSURANCE, progress_callback, websocket_task_id)
            quality_data = await self._step_7_quality_assurance(generated_data)
            
            # Step 8: Export
            await self._update_stage(PipelineStage.EXPORT, progress_callback, websocket_task_id)
            export_data = await self._step_8_export(quality_data, format_type)
            
            # Complete pipeline
            total_time = (datetime.now() - start_time).total_seconds()
            
            final_result = {
                "pipeline_id": pipeline_id,
                "status": "completed",
                "total_processing_time_seconds": total_time,
                "stages_completed": len(self.pipeline_state["stages_completed"]),
                "final_data": export_data,
                "pipeline_metadata": {
                    "input_length": len(input_text),
                    "concepts_extracted": len(concepts),
                    "characterization_dimensions": len(characterization),
                    "total_samples_generated": len(quality_data.get("samples", [])),
                    "format_type": format_type,
                    "agents_used": list(self.agents.keys())
                }
            }
            
            logger.info(f"✅ Pipeline {pipeline_id} completed in {total_time:.2f}s")
            
            # Send WebSocket completion notification
            if websocket_task_id and WEBSOCKET_AVAILABLE:
                await send_pipeline_complete(
                    task_id=websocket_task_id,
                    results=final_result
                )
            
            return final_result
            
        except Exception as e:
            total_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ Pipeline {pipeline_id} failed at stage {self.current_stage}: {e}")
            
            # Send WebSocket error notification
            if websocket_task_id and WEBSOCKET_AVAILABLE:
                await send_pipeline_error(
                    task_id=websocket_task_id,
                    stage=self.current_stage.value if self.current_stage else "unknown",
                    error=str(e)
                )
            
            return {
                "pipeline_id": pipeline_id,
                "status": "failed",
                "error": str(e),
                "failed_at_stage": self.current_stage.value if self.current_stage else "unknown",
                "total_processing_time_seconds": total_time,
                "partial_results": self.pipeline_state.get("results", {})
            }
    
    async def _update_stage(self, stage: PipelineStage, progress_callback: Optional[Callable] = None, websocket_task_id: Optional[str] = None):
        """Update current pipeline stage and notify callback + WebSocket"""
        self.current_stage = stage
        self.pipeline_state["current_stage"] = stage.value
        
        logger.info(f"📍 Pipeline stage: {stage.value}")
        
        progress_data = {
            "current_stage": stage.value,
            "stages_completed": len(self.pipeline_state["stages_completed"]),
            "total_stages": 8,
            "progress": len(self.pipeline_state["stages_completed"]) / 8.0
        }
        
        # Call progress callback
        if progress_callback:
            await progress_callback(progress_data)
        
        # Send WebSocket update if task ID provided
        if websocket_task_id and WEBSOCKET_AVAILABLE:
            await send_pipeline_update(
                task_id=websocket_task_id,
                stage=stage.value,
                progress=progress_data["progress"],
                message=f"Starting {stage.value}",
                data=progress_data
            )
    
    async def _step_1_input_processing(self, input_text: str) -> Dict[str, Any]:
        """Step 1: Process and validate input text"""
        logger.info("📝 Step 1: Input Processing")
        
        processed = {
            "text": input_text.strip(),
            "length": len(input_text),
            "word_count": len(input_text.split()),
            "processing_timestamp": datetime.now().isoformat()
        }
        
        self.pipeline_state["stages_completed"].append("input_processing")
        self.pipeline_state["results"]["input"] = processed
        
        return processed
    
    async def _step_2_concept_extraction(self, text: str) -> List[Dict[str, Any]]:
        """Step 2: Extract 20-50 core concepts"""
        logger.info("🧠 Step 2: Concept Extraction")
        
        concepts = await self.concept_extractor.extract_from_text(text, max_concepts=40)
        
        self.pipeline_state["stages_completed"].append("concept_extraction")
        self.pipeline_state["results"]["concepts"] = concepts
        
        logger.info(f"✅ Extracted {len(concepts)} concepts")
        return concepts
    
    async def _step_3_characterization(self, concepts: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Step 3: Multi-dimensional characterization with 5 agents (SEQUENTIAL)"""
        logger.info("🎯 Step 3: Multi-Dimensional Characterization (Sequential)")
        
        # Extract concept names for agents
        concept_names = [c["name"] for c in concepts]
        
        characterization_results = {}
        accumulated_context = {}
        
        # Run agents sequentially to avoid overwhelming the system
        agent_order = ['geographic', 'cultural', 'linguistic', 'persona', 'domain']
        
        for agent_name in agent_order:
            logger.info(f"🤖 Running {agent_name} agent...")
            
            try:
                agent = self.agents[agent_name]
                suggestions = await agent.process(concept_names, accumulated_context)
                characterization_results[agent_name] = suggestions
                accumulated_context[agent_name] = suggestions
                
                logger.info(f"✅ {agent_name}: {len(suggestions)} suggestions")
                
                # Small delay between agents to be gentle on the system
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.warning(f"⚠️ {agent_name} agent failed: {e}")
                characterization_results[agent_name] = []
        
        self.pipeline_state["stages_completed"].append("characterization")
        self.pipeline_state["results"]["characterization"] = characterization_results
        
        return characterization_results
    
    async def _step_4_human_validation(self, characterization: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Step 4: Human validation (simulated for automated pipeline)"""
        logger.info("👤 Step 4: Human Validation (Simulated)")
        
        # In a full implementation, this would present concepts to user for review
        # For automated pipeline, we simulate basic validation
        
        validated = {}
        for category, suggestions in characterization.items():
            # Simulate validation: take top suggestions and add some variety
            validated[category] = suggestions[:12]  # Limit to 12 per category
        
        self.pipeline_state["stages_completed"].append("human_validation")
        self.pipeline_state["results"]["validated_concepts"] = validated
        
        total_concepts = sum(len(concepts) for concepts in validated.values())
        logger.info(f"✅ Validated {total_concepts} concepts across {len(validated)} dimensions")
        
        return validated
    
    async def _step_5_format_selection(self, format_type: str, samples_per_combination: int) -> Dict[str, Any]:
        """Step 5: Configure generation format and parameters"""
        logger.info(f"📊 Step 5: Format Selection ({format_type})")
        
        config = {
            "format_type": format_type,
            "samples_per_combination": samples_per_combination,
            "complexity_levels": [1, 2, 3],
            "template_loaded": True,
            "configuration_timestamp": datetime.now().isoformat()
        }
        
        self.pipeline_state["stages_completed"].append("format_selection")
        self.pipeline_state["results"]["generation_config"] = config
        
        return config
    
    async def _step_6_generation(self, concept_dimensions: Dict[str, List[str]], 
                                generation_config: Dict[str, Any],
                                max_total_samples: int,
                                websocket_task_id: Optional[str] = None) -> Dict[str, Any]:
        """Step 6: Combinatorial generation"""
        logger.info("⚡ Step 6: Combinatorial Generation")
        
        # Estimate scale
        estimated_samples, stats = self.combinator.estimate_total_samples(
            concept_dimensions,
            generation_config["samples_per_combination"],
            generation_config["complexity_levels"]
        )
        
        logger.info(f"📊 Estimated {estimated_samples:,} samples from {stats['total_combinations']} combinations")
        
        # Limit for system safety
        if estimated_samples > max_total_samples:
            logger.info(f"⚠️ Limiting to {max_total_samples:,} samples")
            estimated_samples = max_total_samples
        
        # Generate combinations for full-scale production
        sample_combinations = self.combinator.generate_combinations(concept_dimensions)
        
        # Limit combinations based on max_total_samples
        max_combinations = max_total_samples // 2  # 2 samples per combination
        sample_combinations = list(sample_combinations)[:max_combinations]
        
        logger.info(f"🎯 Processing {len(sample_combinations)} combinations for {len(sample_combinations)*2} samples")
        
        generated_samples = []
        for i, combo in enumerate(sample_combinations):
            combo_id = combo.get('combination_id', 'unknown')
            progress_msg = f"🎯 Processing combination {i+1:,} of {len(sample_combinations):,} (ID: {combo_id})"
            logger.info(progress_msg)
            
            # Send progress update via WebSocket if available
            if WEBSOCKET_AVAILABLE and websocket_task_id:
                progress_percent = (i / len(sample_combinations)) * 0.5 + 0.5  # Generation is 50-100% of pipeline
                await send_pipeline_update(
                    task_id=websocket_task_id,
                    stage="generation",
                    progress=progress_percent,
                    message=f"Generating samples {i+1:,}/{len(sample_combinations):,}",
                    data={
                        "combination_current": i + 1,
                        "combination_total": len(sample_combinations),
                        "samples_generated": len(generated_samples),
                        "combination_id": combo_id
                    }
                )
            
            try:
                # Generate a few samples per combination for demo
                logger.info(f"📝 Getting template for format: {generation_config['format_type']}")
                template_data = prompt_loader.get_generation_template(
                    generation_config["format_type"],
                    combo,
                    combo.get("complexity_level", 1),
                    2  # Limited samples for pipeline demo
                )
                logger.info(f"✅ Template generated, user prompt length: {len(template_data.get('user', ''))}")
                
                logger.info(f"🤖 Sending to LLM...")
                response = await ollama_client.generate(
                    prompt=template_data['user'],
                    system_prompt=template_data['system'],
                    task_type='generation'
                )
                logger.info(f"✅ LLM response received, length: {len(response)}")
                
                # DEBUG: Save raw LLM response to file
                combo_id = combo.get('combination_id', 'unknown')
                debug_filename = f"debug_generation_{combo_id}.txt"
                try:
                    with open(debug_filename, 'w', encoding='utf-8') as f:
                        f.write(f"=== PROMPT ===\n")
                        f.write(f"System: {template_data.get('system', 'N/A')}\n\n")
                        f.write(f"User: {template_data['user']}\n\n")
                        f.write(f"=== LLM RESPONSE ===\n")
                        f.write(response)
                    logger.info(f"💾 Saved raw LLM response to {debug_filename}")
                except Exception as save_error:
                    logger.warning(f"Failed to save debug file: {save_error}")
                
                # Parse and add samples
                parsed_samples = self._parse_generation_response(response, combo)
                generated_samples.extend(parsed_samples)
                
            except Exception as e:
                logger.warning(f"Generation failed for combination {combo.get('combination_id')}: {e}")
                continue
        
        generation_result = {
            "samples": generated_samples,
            "total_generated": len(generated_samples),
            "combinations_processed": len(sample_combinations),
            "format_type": generation_config["format_type"],
            "generation_timestamp": datetime.now().isoformat()
        }
        
        self.pipeline_state["stages_completed"].append("generation")
        self.pipeline_state["results"]["generation"] = generation_result
        
        logger.info(f"✅ Generated {len(generated_samples)} samples")
        return generation_result
    
    async def _step_7_quality_assurance(self, generated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Step 7: Quality assurance and filtering"""
        logger.info("🔍 Step 7: Quality Assurance")
        
        samples = generated_data.get("samples", [])
        
        # Basic quality filtering
        quality_samples = []
        for sample in samples:
            if self._is_quality_sample(sample):
                quality_samples.append(sample)
        
        quality_result = {
            "samples": quality_samples,
            "original_count": len(samples),
            "quality_count": len(quality_samples),
            "quality_rate": len(quality_samples) / len(samples) if samples else 0,
            "quality_timestamp": datetime.now().isoformat()
        }
        
        self.pipeline_state["stages_completed"].append("quality_assurance")
        self.pipeline_state["results"]["quality"] = quality_result
        
        logger.info(f"✅ Quality check: {len(quality_samples)}/{len(samples)} samples passed")
        return quality_result
    
    async def _step_8_export(self, quality_data: Dict[str, Any], format_type: str) -> Dict[str, Any]:
        """Step 8: Format for HuggingFace export"""
        logger.info("📦 Step 8: HuggingFace Export Formatting")
        
        export_data = {
            "format": format_type,
            "data": quality_data.get("samples", []),
            "metadata": {
                "total_samples": len(quality_data.get("samples", [])),
                "format_type": format_type,
                "generated_by": "synthetic_data_platform",
                "export_timestamp": datetime.now().isoformat(),
                "pipeline_id": self.pipeline_state["pipeline_id"]
            }
        }
        
        self.pipeline_state["stages_completed"].append("export")
        self.pipeline_state["results"]["export"] = export_data
        
        logger.info(f"✅ Export ready: {len(export_data['data'])} samples in {format_type} format")
        return export_data
    
    def _parse_generation_response(self, response: str, combination: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse generated samples from LLM response"""
        json_data = ollama_client.parse_json_response(response)
        
        if json_data and isinstance(json_data, list):
            samples = []
            for item in json_data:
                if isinstance(item, dict):
                    item.update({
                        "combination_id": combination.get("combination_id"),
                        "pipeline_generated": True
                    })
                    samples.append(item)
            return samples
        
        # Fallback
        return [{
            "content": response.strip(),
            "combination_id": combination.get("combination_id"),
            "pipeline_generated": True,
            "parsed_as": "fallback"
        }]
    
    def _is_quality_sample(self, sample: Dict[str, Any]) -> bool:
        """Basic quality validation"""
        # Check for minimum content
        for key in ['instruction', 'response', 'question', 'answer', 'text', 'content']:
            if key in sample:
                content = str(sample[key]).strip()
                if len(content) < 10 or len(content) > 3000:
                    return False
        return True
    
    async def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status"""
        return {
            "current_stage": self.current_stage.value if self.current_stage else None,
            "stages_completed": self.pipeline_state.get("stages_completed", []),
            "total_stages": 8,
            "progress_percentage": len(self.pipeline_state.get("stages_completed", [])) / 8 * 100
        }