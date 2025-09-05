#!/usr/bin/env python3
"""
Synthetic Data Platform - Main FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import yaml
from pathlib import Path

# Import API routers
from api.extraction import router as extraction_router
from api.characterization import router as characterization_router
from api.generation import router as generation_router
from api.validation import router as validation_router

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
config_path = Path(__file__).parent.parent / "config" / "models.yaml"
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

app = FastAPI(
    title="Synthetic Data Platform",
    description="AI-powered combinatorial synthetic data generation with specialized agents",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint with platform information"""
    return {
        "message": "🧠 Synthetic Data Platform",
        "status": "ready",
        "version": "1.0.0",
        "pipeline": {
            "1": "Input Processing",
            "2": "Concept Extraction (20-50 concepts)",
            "3": "Multi-Dimensional Characterization (5 agents)",
            "4": "Human Validation + Customization",
            "5": "Format Selection (DPO, SFT, Q&A, Raw)",
            "6": "Combinatorial Generation (50K+ samples)",
            "7": "Quality Assurance",
            "8": "HuggingFace Export"
        },
        "agents": [
            "Geographic Agent", 
            "Linguistic Agent", 
            "Cultural Agent", 
            "Persona Agent", 
            "Domain Agent"
        ],
        "current_model": config["default_model"]
    }

@app.get("/health")
async def health_check():
    """Health check with model status"""
    return {
        "status": "healthy",
        "model": config["default_model"],
        "ollama_url": config["ollama_url"],
        "agents_ready": True,
        "prompt_templates": "loaded"
    }

# Include API routes
app.include_router(extraction_router, prefix="/api/extraction", tags=["extraction"])
app.include_router(characterization_router, prefix="/api/characterization", tags=["characterization"]) 
app.include_router(generation_router, prefix="/api/generation", tags=["generation"])
app.include_router(validation_router, prefix="/api/validation", tags=["validation"])

if __name__ == "__main__":
    import uvicorn
    logger.info(f"🚀 Starting Synthetic Data Platform with {config['default_model']}")
    logger.info("📊 50K+ sample generation capability enabled")
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )