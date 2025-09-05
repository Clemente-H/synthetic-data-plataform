#!/usr/bin/env python3
"""
Characterization API - Step 3: Multi-Dimensional Characterization with 5 Specialized Agents
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
import asyncio
from datetime import datetime

from agents.geographic_agent import GeographicAgent
from agents.cultural_agent import CulturalAgent
from agents.linguistic_agent import LinguisticAgent
from agents.persona_agent import PersonaAgent
from agents.domain_agent import DomainAgent

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize all agents
agents = {
    'geographic': GeographicAgent(),
    'cultural': CulturalAgent(),
    'linguistic': LinguisticAgent(),
    'persona': PersonaAgent(),
    'domain': DomainAgent()
}

# Request/Response Models
class CharacterizationRequest(BaseModel):
    core_concepts: List[str] = Field(..., description="List of core concepts from extraction", min_items=1)
    agents_to_run: List[str] = Field(
        default=['geographic', 'cultural', 'linguistic', 'persona', 'domain'],
        description="List of agents to run for characterization"
    )
    max_suggestions_per_agent: int = Field(15, description="Max suggestions per agent", ge=5, le=20)
    run_parallel: bool = Field(True, description="Run agents in parallel for speed")

class AgentResult(BaseModel):
    agent_type: str
    suggestions: List[str]
    processing_time_seconds: float
    status: str
    error_message: Optional[str] = None

class CharacterizationResponse(BaseModel):
    status: str
    agent_results: Dict[str, AgentResult]
    total_suggestions: int
    total_processing_time_seconds: float
    pipeline_metadata: Optional[Dict[str, Any]] = None

@router.post("/characterize", response_model=CharacterizationResponse)
async def characterize_concepts(request: CharacterizationRequest):
    """
    Step 3: Multi-Dimensional Characterization
    
    Runs specialized agents to characterize concepts across multiple dimensions:
    - Geographic: Location-specific contexts, regulations, regional variations
    - Cultural: Cultural references, expressions, social contexts
    - Linguistic: Language variations, communication styles, terminology
    - Persona: User archetypes, demographics, role perspectives  
    - Domain: Technical concepts, industry terminology, expertise levels
    """
    start_time = datetime.now()
    
    try:
        logger.info(f"🎯 Starting characterization with {len(request.agents_to_run)} agents")
        logger.info(f"Core concepts: {request.core_concepts}")
        
        # Validate agents
        invalid_agents = [agent for agent in request.agents_to_run if agent not in agents]
        if invalid_agents:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid agents: {invalid_agents}. Available: {list(agents.keys())}"
            )
        
        agent_results = {}
        total_suggestions = 0
        
        if request.run_parallel:
            # Run agents in parallel for speed
            results = await _run_agents_parallel(
                request.core_concepts, 
                request.agents_to_run,
                request.max_suggestions_per_agent
            )
            agent_results = results
        else:
            # Run agents sequentially (allows context passing between agents)
            results = await _run_agents_sequential(
                request.core_concepts,
                request.agents_to_run, 
                request.max_suggestions_per_agent
            )
            agent_results = results
        
        # Calculate totals
        total_suggestions = sum(len(result.suggestions) for result in agent_results.values())
        total_time = (datetime.now() - start_time).total_seconds()
        
        # Create pipeline metadata
        pipeline_metadata = {
            "core_concepts_count": len(request.core_concepts),
            "agents_requested": request.agents_to_run,
            "agents_successful": [name for name, result in agent_results.items() if result.status == "success"],
            "agents_failed": [name for name, result in agent_results.items() if result.status == "error"],
            "execution_mode": "parallel" if request.run_parallel else "sequential",
            "characterization_timestamp": start_time.isoformat(),
            "suggestions_distribution": {name: len(result.suggestions) for name, result in agent_results.items()}
        }
        
        logger.info(f"✅ Characterization complete: {total_suggestions} total suggestions in {total_time:.2f}s")
        
        return CharacterizationResponse(
            status="success" if agent_results else "partial_failure",
            agent_results=agent_results,
            total_suggestions=total_suggestions,
            total_processing_time_seconds=total_time,
            pipeline_metadata=pipeline_metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        total_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"❌ Characterization failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Characterization failed",
                "message": str(e),
                "processing_time": total_time
            }
        )

async def _run_agents_parallel(core_concepts: List[str], agent_names: List[str], 
                              max_suggestions: int) -> Dict[str, AgentResult]:
    """
    Run agents in parallel for maximum speed
    """
    logger.info("⚡ Running agents in parallel mode")
    
    # Create tasks for all agents
    tasks = []
    for agent_name in agent_names:
        task = _run_single_agent(agent_name, core_concepts, {}, max_suggestions)
        tasks.append((agent_name, task))
    
    results = {}
    
    # Wait for all tasks to complete
    for agent_name, task in tasks:
        try:
            result = await task
            results[agent_name] = result
        except Exception as e:
            logger.error(f"Agent {agent_name} failed: {e}")
            results[agent_name] = AgentResult(
                agent_type=agent_name,
                suggestions=[],
                processing_time_seconds=0.0,
                status="error",
                error_message=str(e)
            )
    
    return results

async def _run_agents_sequential(core_concepts: List[str], agent_names: List[str],
                                max_suggestions: int) -> Dict[str, AgentResult]:
    """
    Run agents sequentially, allowing context to be passed between agents
    """
    logger.info("🔄 Running agents in sequential mode")
    
    results = {}
    accumulated_context = {}
    
    # Define execution order for optimal context passing
    execution_order = ['geographic', 'cultural', 'linguistic', 'persona', 'domain']
    ordered_agents = [agent for agent in execution_order if agent in agent_names]
    remaining_agents = [agent for agent in agent_names if agent not in ordered_agents]
    final_order = ordered_agents + remaining_agents
    
    for agent_name in final_order:
        try:
            result = await _run_single_agent(agent_name, core_concepts, accumulated_context, max_suggestions)
            results[agent_name] = result
            
            # Add successful results to context for next agents
            if result.status == "success" and result.suggestions:
                accumulated_context[agent_name] = result.suggestions
                
        except Exception as e:
            logger.error(f"Agent {agent_name} failed: {e}")
            results[agent_name] = AgentResult(
                agent_type=agent_name,
                suggestions=[],
                processing_time_seconds=0.0,
                status="error",
                error_message=str(e)
            )
    
    return results

async def _run_single_agent(agent_name: str, core_concepts: List[str], 
                           context: Dict[str, List[str]], max_suggestions: int) -> AgentResult:
    """
    Run a single agent and return structured result
    """
    start_time = datetime.now()
    
    try:
        agent = agents[agent_name]
        suggestions = await agent.process(core_concepts, context)
        
        # Limit suggestions
        limited_suggestions = suggestions[:max_suggestions]
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ {agent_name.title()} agent: {len(limited_suggestions)} suggestions in {processing_time:.2f}s")
        
        return AgentResult(
            agent_type=agent_name,
            suggestions=limited_suggestions,
            processing_time_seconds=processing_time,
            status="success"
        )
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"❌ {agent_name.title()} agent failed: {e}")
        
        return AgentResult(
            agent_type=agent_name,
            suggestions=[],
            processing_time_seconds=processing_time,
            status="error",
            error_message=str(e)
        )

@router.post("/characterize-single-agent")
async def characterize_single_agent(
    agent_name: str,
    core_concepts: List[str],
    context: Dict[str, List[str]] = {},
    max_suggestions: int = 15
):
    """
    Run a single agent for testing or individual characterization
    """
    try:
        if agent_name not in agents:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid agent: {agent_name}. Available: {list(agents.keys())}"
            )
        
        result = await _run_single_agent(agent_name, core_concepts, context, max_suggestions)
        
        return {
            "agent_type": agent_name,
            "suggestions": result.suggestions,
            "processing_time_seconds": result.processing_time_seconds,
            "status": result.status,
            "core_concepts_used": core_concepts,
            "context_provided": list(context.keys()) if context else []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Single agent characterization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents")
async def list_available_agents():
    """
    List all available characterization agents and their descriptions
    """
    return {
        "available_agents": {
            "geographic": {
                "description": "Location-specific regulations, cultural norms, legal frameworks",
                "specialization": "Regional variations and geographic contexts"
            },
            "cultural": {
                "description": "Cultural references, expressions, social contexts, web trends",
                "specialization": "Cultural nuances and social context variations"
            },
            "linguistic": {
                "description": "Language variations, communication styles, terminology",
                "specialization": "Linguistic patterns and formality levels"
            },
            "persona": {
                "description": "User archetypes, demographics, role perspectives",
                "specialization": "User personas and demographic variations"
            },
            "domain": {
                "description": "Technical concepts, industry terminology, expertise levels",
                "specialization": "Domain-specific knowledge and technical depth"
            }
        },
        "execution_modes": ["parallel", "sequential"],
        "recommended_order": ["geographic", "cultural", "linguistic", "persona", "domain"]
    }

@router.get("/health")
async def characterization_health():
    """Health check for characterization service"""
    try:
        # Test one agent to check overall health
        test_agent = agents['geographic']
        is_healthy = await test_agent.client.check_health()
        
        return {
            "status": "healthy" if is_healthy else "degraded",
            "service": "multi_dimensional_characterization",
            "agents_available": list(agents.keys()),
            "total_agents": len(agents),
            "ollama_connected": is_healthy,
            "capabilities": [
                "Parallel agent execution",
                "Sequential context-aware execution", 
                "Individual agent testing",
                "Multi-dimensional concept enrichment"
            ]
        }
    except Exception as e:
        logger.error(f"Characterization health check failed: {e}")
        raise HTTPException(status_code=503, detail="Characterization service unavailable")