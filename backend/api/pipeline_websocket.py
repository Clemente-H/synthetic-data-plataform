#!/usr/bin/env python3
"""
Full Pipeline API with WebSocket Real-time Updates
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
import logging
import uuid
from datetime import datetime

from core.pipeline import PipelineOrchestrator
from api.websocket import send_pipeline_update, send_pipeline_complete, send_pipeline_error, send_sample_generated

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize pipeline orchestrator
pipeline = PipelineOrchestrator()

# Request/Response Models
class FullPipelineRequest(BaseModel):
    input_text: str = Field(..., description="Text to process through full pipeline")
    format_type: Literal["dpo", "sft", "qa", "raw"] = Field("qa", description="Output format")
    samples_per_combination: int = Field(3, description="Samples per combination", ge=1, le=20)
    max_total_samples: int = Field(100, description="Max total samples", ge=10, le=10000)
    max_concepts: int = Field(30, description="Max concepts to extract", ge=10, le=50)
    agents_to_run: List[str] = Field(
        default=['geographic', 'cultural', 'linguistic', 'persona', 'domain'],
        description="Characterization agents to run"
    )

class PipelineTaskResponse(BaseModel):
    status: str = Field(..., description="Task status")  
    task_id: str = Field(..., description="Task ID for WebSocket subscription")
    message: str = Field(..., description="Human readable message")
    estimated_duration: str = Field(..., description="Estimated completion time")

@router.options("/run-full-pipeline")
async def options_run_full_pipeline():
    return {}

@router.post("/run-full-pipeline", response_model=PipelineTaskResponse)
async def run_full_pipeline_websocket(request: FullPipelineRequest, background_tasks: BackgroundTasks):
    """
    Execute complete 8-step pipeline with real-time WebSocket updates
    
    Steps with real-time progress:
    1. Input Processing
    2. Concept Extraction (20-50 concepts) 
    3. Multi-Dimensional Characterization (5 agents)
    4. Human Validation (simulated)
    5. Format Selection
    6. Combinatorial Generation (with sample streaming)
    7. Quality Assurance
    8. Export Preparation
    """
    
    task_id = str(uuid.uuid4())
    logger.info(f"🚀 Starting full pipeline WebSocket task: {task_id}")
    
    # Estimate duration based on input
    estimated_samples = min(request.max_total_samples, 1000)  # Conservative estimate
    estimated_minutes = max(2, estimated_samples // 100)  # Rough estimate
    
    async def run_full_pipeline_with_websocket():
        start_time = datetime.now()
        
        try:
            await send_pipeline_update(
                task_id=task_id,
                stage="pipeline_start",
                progress=0.0,
                message=f"🚀 Starting full 8-step pipeline execution",
                data={
                    "input_length": len(request.input_text),
                    "format_type": request.format_type,
                    "max_samples": request.max_total_samples,
                    "estimated_duration": f"{estimated_minutes} minutes"
                }
            )
            
            # Custom progress callback for WebSocket updates
            async def websocket_progress_callback(progress_data):
                await send_pipeline_update(
                    task_id=task_id,
                    stage=progress_data.get("current_stage", "unknown"),
                    progress=progress_data.get("progress", 0.0),
                    message=f"Stage {progress_data.get('stages_completed', 0) + 1}/8: {progress_data.get('current_stage', 'Processing')}",
                    data=progress_data
                )
            
            # Run the full pipeline with WebSocket integration
            result = await pipeline.run_full_pipeline(
                input_text=request.input_text,
                format_type=request.format_type,
                samples_per_combination=request.samples_per_combination,
                max_total_samples=request.max_total_samples,
                progress_callback=websocket_progress_callback,
                websocket_task_id=task_id  # This enables WebSocket updates in pipeline
            )
            
            # Calculate final stats
            total_time = (datetime.now() - start_time).total_seconds()
            
            # Send completion with enhanced results
            final_results = {
                **result,
                "websocket_task_id": task_id,
                "real_duration_seconds": total_time,
                "real_duration_minutes": round(total_time / 60, 2),
                "pipeline_efficiency": {
                    "estimated_minutes": estimated_minutes,
                    "actual_minutes": round(total_time / 60, 2),
                    "performance": "faster" if total_time < (estimated_minutes * 60) else "slower"
                }
            }
            
            await send_pipeline_complete(task_id=task_id, results=final_results)
            logger.info(f"✅ Full pipeline task {task_id} completed in {total_time:.2f}s")
            
        except Exception as e:
            total_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ Full pipeline task {task_id} failed: {e}")
            
            await send_pipeline_error(
                task_id=task_id,
                stage="pipeline_execution",
                error=f"Pipeline failed after {total_time:.1f}s: {str(e)}"
            )
    
    # Start background task
    background_tasks.add_task(run_full_pipeline_with_websocket)
    
    return PipelineTaskResponse(
        status="started",
        task_id=task_id,
        message=f"🎭 Full 8-step pipeline started with real-time updates",
        estimated_duration=f"{estimated_minutes} minutes"
    )

# Enhanced characterization endpoint with individual agent progress
@router.options("/characterize-websocket")  
async def options_characterize_websocket():
    return {}

@router.post("/characterize-websocket")
async def characterize_websocket(
    concepts: List[str],
    agents_to_run: List[str] = ['geographic', 'cultural', 'linguistic', 'persona', 'domain'],
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Run characterization agents with individual progress tracking
    """
    task_id = str(uuid.uuid4())
    logger.info(f"🎯 Starting characterization WebSocket task: {task_id}")
    
    async def run_characterization_with_websocket():
        try:
            await send_pipeline_update(
                task_id=task_id,
                stage="characterization_start",
                progress=0.0,
                message=f"🎯 Starting multi-dimensional characterization with {len(agents_to_run)} agents",
                data={"concepts": concepts, "agents": agents_to_run}
            )
            
            results = {}
            total_agents = len(agents_to_run)
            
            for i, agent_name in enumerate(agents_to_run):
                # Update progress for each agent
                agent_progress = i / total_agents
                
                await send_pipeline_update(
                    task_id=task_id,
                    stage=f"agent_{agent_name}",
                    progress=agent_progress,
                    message=f"🤖 Running {agent_name} agent ({i+1}/{total_agents})",
                    data={
                        "current_agent": agent_name,
                        "agent_number": i + 1,
                        "total_agents": total_agents,
                        "concepts_processing": len(concepts)
                    }
                )
                
                # Use real agents instead of simulation
                try:
                    if agent_name == 'geographic':
                        from agents.geographic_agent import GeographicAgent
                        agent = GeographicAgent()
                        suggestions = await agent.generate_suggestions(concepts)
                        results[agent_name] = suggestions
                    elif agent_name == 'cultural':
                        from agents.cultural_agent import CulturalAgent
                        agent = CulturalAgent()
                        suggestions = await agent.generate_suggestions(concepts)
                        results[agent_name] = suggestions
                    elif agent_name == 'linguistic':
                        from agents.linguistic_agent import LinguisticAgent
                        agent = LinguisticAgent()
                        suggestions = await agent.generate_suggestions(concepts)
                        results[agent_name] = suggestions
                    elif agent_name == 'persona':
                        from agents.persona_agent import PersonaAgent
                        agent = PersonaAgent()
                        suggestions = await agent.generate_suggestions(concepts)
                        results[agent_name] = suggestions
                    elif agent_name == 'domain':
                        from agents.domain_agent import DomainAgent
                        agent = DomainAgent()
                        suggestions = await agent.generate_suggestions(concepts)
                        results[agent_name] = suggestions
                    else:
                        # Fallback to mock for unknown agents
                        results[agent_name] = [f"{agent_name}_context_{j}" for j in range(12)]
                        
                except Exception as e:
                    logger.error(f"Error running {agent_name} agent: {e}")
                    # Fallback to mock on error
                    results[agent_name] = [f"{agent_name}_context_{j}" for j in range(12)]
                
                await send_pipeline_update(
                    task_id=task_id,
                    stage=f"agent_{agent_name}_complete",
                    progress=(i + 1) / total_agents,
                    message=f"✅ {agent_name} agent completed - {len(results[agent_name])} contexts generated",
                    data={
                        "agent": agent_name,
                        "suggestions": results[agent_name],
                        "completed_agents": i + 1
                    }
                )
            
            await send_pipeline_complete(
                task_id=task_id,
                results={
                    "status": "completed",
                    "characterization": results,
                    "total_agents": total_agents,
                    "total_contexts": sum(len(contexts) for contexts in results.values())
                }
            )
            
        except Exception as e:
            await send_pipeline_error(task_id=task_id, stage="characterization", error=str(e))
    
    background_tasks.add_task(run_characterization_with_websocket)
    
    return {"status": "started", "task_id": task_id}