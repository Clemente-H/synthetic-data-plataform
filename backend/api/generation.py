#!/usr/bin/env python3
"""
Generation API - Steps 6-8: Combinatorial Generation + Quality Assurance + Export
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
import logging
import asyncio
import json
import io
from datetime import datetime
import uuid

from core.combinator import ConceptCombinator
from utils.ollama_client import ollama_client
from utils.prompt_loader import prompt_loader

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize combinator
combinator = ConceptCombinator(max_combinations=50000)  # Support up to 50K combinations

# Request/Response Models
class GenerationRequest(BaseModel):
    concept_dimensions: Dict[str, List[str]] = Field(
        ..., 
        description="Concept dimensions from characterization step"
    )
    format_type: Literal["dpo", "sft", "qa", "raw"] = Field(
        "qa", 
        description="Output format for synthetic data"
    )
    samples_per_combination: int = Field(
        3, 
        description="Samples to generate per concept combination", 
        ge=1, le=20
    )
    complexity_levels: List[int] = Field(
        [1, 2, 3], 
        description="Complexity levels to generate"
    )
    max_total_samples: int = Field(
        10000, 
        description="Maximum total samples to generate", 
        ge=100, le=100000
    )
    include_metadata: bool = Field(True, description="Include generation metadata")
    quality_check: bool = Field(True, description="Run quality assurance")

class GenerationResponse(BaseModel):
    task_id: str
    status: Literal["pending", "running", "completed", "failed"]
    estimated_samples: int
    estimated_combinations: int
    processing_info: Dict[str, Any]
    download_urls: Optional[Dict[str, str]] = None

class GenerationStatus(BaseModel):
    task_id: str
    status: str
    progress: Dict[str, Any]
    current_stage: str
    samples_generated: int
    total_estimated: int
    error_message: Optional[str] = None

# In-memory task storage (in production, use Redis or database)
generation_tasks: Dict[str, Dict[str, Any]] = {}

@router.post("/generate", response_model=GenerationResponse)
async def generate_synthetic_data(request: GenerationRequest, background_tasks: BackgroundTasks):
    """
    Steps 6-8: Massive Combinatorial Generation
    
    - Step 6: Generate all possible concept combinations
    - Step 7: Create synthetic data for each combination using templates  
    - Step 8: Quality assurance and export formatting
    
    Returns immediately with task_id for background processing
    """
    task_id = str(uuid.uuid4())
    start_time = datetime.now()
    
    try:
        logger.info(f"🚀 Starting massive synthetic data generation (task: {task_id})")
        
        # Estimate total samples and combinations
        estimated_samples, stats = combinator.estimate_total_samples(
            concept_dimensions=request.concept_dimensions,
            samples_per_combination=request.samples_per_combination,
            complexity_levels=request.complexity_levels
        )
        
        # Apply limit
        if estimated_samples > request.max_total_samples:
            logger.warning(f"Estimated samples ({estimated_samples:,}) exceeds limit ({request.max_total_samples:,})")
            estimated_samples = request.max_total_samples
        
        # Initialize task tracking
        generation_tasks[task_id] = {
            "status": "pending",
            "created_at": start_time.isoformat(),
            "request": request.dict(),
            "stats": stats,
            "progress": {
                "combinations_processed": 0,
                "total_combinations": stats["total_combinations"],
                "samples_generated": 0,
                "estimated_samples": estimated_samples,
                "current_stage": "initializing",
                "percentage": 0.0
            }
        }
        
        # Start background generation
        background_tasks.add_task(
            _run_massive_generation,
            task_id,
            request,
            stats
        )
        
        logger.info(f"✅ Task {task_id} queued: {estimated_samples:,} estimated samples")
        
        return GenerationResponse(
            task_id=task_id,
            status="pending",
            estimated_samples=estimated_samples,
            estimated_combinations=stats["total_combinations"],
            processing_info={
                "format_type": request.format_type,
                "dimensions_used": len([k for k, v in request.concept_dimensions.items() if v]),
                "complexity_levels": request.complexity_levels,
                "samples_per_combination": request.samples_per_combination,
                "processing_mode": "background_massive_scale",
                "estimated_duration_minutes": max(1, estimated_samples // 1000)  # Rough estimate
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Generation initialization failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Generation initialization failed",
                "message": str(e),
                "task_id": task_id
            }
        )

async def _run_massive_generation(task_id: str, request: GenerationRequest, stats: Dict[str, Any]):
    """
    Background task for massive scale generation (50K+ samples)
    """
    try:
        task = generation_tasks[task_id]
        task["status"] = "running"
        task["started_at"] = datetime.now().isoformat()
        
        logger.info(f"🔄 Starting massive generation for task {task_id}")
        
        # Update progress
        task["progress"]["current_stage"] = "generating_combinations"
        
        all_generated_samples = []
        combinations_processed = 0
        
        # Generate in batches to manage memory
        batch_size = min(100, stats["total_combinations"] // 10)  # Dynamic batch size
        
        async for combination_batch in _generate_combination_batches(
            request.concept_dimensions, 
            request.complexity_levels,
            batch_size
        ):
            # Generate samples for this batch of combinations
            batch_samples = await _generate_samples_for_combinations(
                combination_batch,
                request.format_type, 
                request.samples_per_combination
            )
            
            all_generated_samples.extend(batch_samples)
            combinations_processed += len(combination_batch)
            
            # Update progress
            progress = (combinations_processed / stats["total_combinations"]) * 100
            task["progress"].update({
                "combinations_processed": combinations_processed,
                "samples_generated": len(all_generated_samples),
                "percentage": min(progress, 100),
                "current_stage": f"processing_batch_{combinations_processed // batch_size}"
            })
            
            # Check if we've hit the sample limit
            if len(all_generated_samples) >= request.max_total_samples:
                logger.info(f"Reached sample limit: {len(all_generated_samples)}")
                break
        
        # Quality assurance step
        if request.quality_check:
            task["progress"]["current_stage"] = "quality_assurance"
            all_generated_samples = await _quality_assurance(all_generated_samples)
        
        # Export formatting step  
        task["progress"]["current_stage"] = "export_formatting"
        export_data = await _format_for_export(all_generated_samples, request.format_type)
        
        # Store results
        task.update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "results": {
                "generated_samples": all_generated_samples,
                "export_data": export_data,
                "final_stats": {
                    "total_samples": len(all_generated_samples),
                    "combinations_used": combinations_processed,
                    "format": request.format_type,
                    "quality_checked": request.quality_check
                }
            }
        })
        
        # Update final progress
        task["progress"].update({
            "percentage": 100,
            "current_stage": "completed",
            "samples_generated": len(all_generated_samples)
        })
        
        logger.info(f"✅ Task {task_id} completed: {len(all_generated_samples):,} samples generated")
        
    except Exception as e:
        logger.error(f"❌ Task {task_id} failed: {e}")
        generation_tasks[task_id].update({
            "status": "failed",
            "failed_at": datetime.now().isoformat(),
            "error": str(e)
        })

async def _generate_combination_batches(concept_dimensions: Dict[str, List[str]], 
                                       complexity_levels: List[int],
                                       batch_size: int):
    """
    Generate combinations in batches for memory efficiency
    """
    async for batch in asyncio.to_thread(
        combinator.generate_batched_combinations,
        concept_dimensions,
        batch_size,
        complexity_levels
    ):
        yield batch

async def _generate_samples_for_combinations(combinations: List[Dict[str, Any]], 
                                           format_type: str,
                                           samples_per_combination: int) -> List[Dict[str, Any]]:
    """
    Generate synthetic data samples for a batch of combinations
    """
    all_samples = []
    
    for combination in combinations:
        try:
            # Get appropriate prompt template
            template_data = prompt_loader.get_generation_template(
                format_type,
                combination,
                combination.get('complexity_level', 1),
                samples_per_combination
            )
            
            # Generate samples using Ollama
            response = await ollama_client.generate(
                prompt=template_data['user'],
                system_prompt=template_data['system'],
                task_type='generation'
            )
            
            # Parse generated samples
            samples = _parse_generated_samples(response, combination)
            all_samples.extend(samples)
            
        except Exception as e:
            logger.warning(f"Failed to generate for combination {combination.get('combination_id')}: {e}")
            # Continue with other combinations
            continue
    
    return all_samples

def _parse_generated_samples(response: str, combination: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parse generated samples from LLM response
    """
    # Try to parse JSON
    json_data = ollama_client.parse_json_response(response)
    
    if json_data and isinstance(json_data, list):
        samples = []
        for item in json_data:
            if isinstance(item, dict):
                # Add combination metadata
                item.update({
                    "combination_id": combination.get("combination_id"),
                    "complexity_level": combination.get("complexity_level"),
                    "generation_timestamp": datetime.now().isoformat()
                })
                samples.append(item)
        return samples
    
    # Fallback: create a single sample from the response
    return [{
        "content": response.strip(),
        "combination_id": combination.get("combination_id"),
        "complexity_level": combination.get("complexity_level"),
        "generation_timestamp": datetime.now().isoformat(),
        "parsed_as": "fallback_text"
    }]

async def _quality_assurance(samples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Basic quality assurance filtering
    In production, this would use BERT-based quality models
    """
    logger.info(f"🔍 Running quality assurance on {len(samples)} samples")
    
    filtered_samples = []
    
    for sample in samples:
        # Basic quality checks
        if _is_sample_quality(sample):
            filtered_samples.append(sample)
    
    logger.info(f"✅ QA complete: {len(filtered_samples)}/{len(samples)} samples passed")
    return filtered_samples

def _is_sample_quality(sample: Dict[str, Any]) -> bool:
    """
    Basic quality validation for a sample
    """
    # Check for minimum content
    for key in ['instruction', 'response', 'question', 'answer', 'text', 'content']:
        if key in sample:
            content = str(sample[key]).strip()
            if len(content) < 10:  # Too short
                return False
            if len(content) > 5000:  # Too long
                return False
    
    return True

async def _format_for_export(samples: List[Dict[str, Any]], format_type: str) -> Dict[str, Any]:
    """
    Format samples for HuggingFace export
    """
    logger.info(f"📦 Formatting {len(samples)} samples for export ({format_type})")
    
    # Basic export formatting
    export_data = {
        "format": format_type,
        "total_samples": len(samples),
        "data": samples,
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "format_type": format_type,
            "total_samples": len(samples)
        }
    }
    
    return export_data

@router.get("/status/{task_id}", response_model=GenerationStatus)
async def get_generation_status(task_id: str):
    """
    Get the status of a generation task
    """
    if task_id not in generation_tasks:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    task = generation_tasks[task_id]
    
    return GenerationStatus(
        task_id=task_id,
        status=task["status"],
        progress=task.get("progress", {}),
        current_stage=task.get("progress", {}).get("current_stage", "unknown"),
        samples_generated=task.get("progress", {}).get("samples_generated", 0),
        total_estimated=task.get("progress", {}).get("estimated_samples", 0),
        error_message=task.get("error")
    )

@router.get("/download/{task_id}")
async def download_results(task_id: str, format: Literal["json", "jsonl"] = "jsonl"):
    """
    Download completed generation results
    """
    if task_id not in generation_tasks:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    task = generation_tasks[task_id]
    
    if task["status"] != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Task {task_id} not completed (status: {task['status']})"
        )
    
    results = task.get("results", {}).get("export_data", {})
    
    if format == "json":
        content = json.dumps(results, indent=2)
        media_type = "application/json"
        filename = f"synthetic_data_{task_id}.json"
    else:  # jsonl
        lines = []
        for sample in results.get("data", []):
            lines.append(json.dumps(sample))
        content = "\n".join(lines)
        media_type = "application/x-jsonlines"
        filename = f"synthetic_data_{task_id}.jsonl"
    
    # Create streaming response
    buffer = io.BytesIO(content.encode('utf-8'))
    
    return StreamingResponse(
        io.BytesIO(content.encode('utf-8')),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/health")
async def generation_health():
    """Health check for generation service"""
    try:
        is_healthy = await ollama_client.check_health()
        
        return {
            "status": "healthy" if is_healthy else "degraded",
            "service": "massive_synthetic_generation",
            "combinator_ready": True,
            "max_combinations_supported": combinator.max_combinations,
            "supported_formats": ["dpo", "sft", "qa", "raw"],
            "ollama_connected": is_healthy,
            "active_tasks": len(generation_tasks),
            "capabilities": [
                "Combinatorial generation (50K+ samples)",
                "Multiple output formats",
                "Quality assurance integration",
                "HuggingFace export compatibility",
                "Background processing with progress tracking"
            ]
        }
    except Exception as e:
        logger.error(f"Generation health check failed: {e}")
        raise HTTPException(status_code=503, detail="Generation service unavailable")

@router.delete("/tasks/{task_id}")
async def cleanup_task(task_id: str):
    """
    Clean up a completed or failed task
    """
    if task_id not in generation_tasks:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    del generation_tasks[task_id]
    
    return {"message": f"Task {task_id} cleaned up successfully"}