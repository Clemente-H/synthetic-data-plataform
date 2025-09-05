#!/usr/bin/env python3
"""
Extraction API - Steps 1-2: Input Processing + Concept Extraction
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
import logging
import asyncio
from datetime import datetime

from agents.concept_extractor import ConceptExtractor

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize concept extractor
concept_extractor = ConceptExtractor()

# Request/Response Models
class ExtractionRequest(BaseModel):
    input_text: str = Field(..., description="User input text to extract concepts from", min_length=10)
    max_concepts: int = Field(30, description="Maximum concepts to extract", ge=10, le=50)
    include_metadata: bool = Field(True, description="Include extraction metadata")

class ConceptResponse(BaseModel):
    name: str
    relevance: int
    category: str
    description: str

class ExtractionResponse(BaseModel):
    status: str
    concepts: List[ConceptResponse]
    extraction_metadata: Optional[Dict[str, Any]] = None
    processing_time_seconds: float
    total_concepts_extracted: int

@router.post("/extract-concepts", response_model=ExtractionResponse)
async def extract_concepts(request: ExtractionRequest):
    """
    Step 2: Extract 20-50 core concepts from user input text
    
    This is the second step in the pipeline where we identify key concepts
    that will be used for multi-dimensional characterization
    """
    start_time = datetime.now()
    
    try:
        logger.info(f"🧠 Starting concept extraction from {len(request.input_text)} characters")
        
        # Extract concepts using the specialized agent
        raw_concepts = await concept_extractor.extract_from_text(
            input_text=request.input_text,
            max_concepts=request.max_concepts
        )
        
        # Convert to response format
        concepts = [
            ConceptResponse(
                name=concept['name'],
                relevance=concept['relevance'],
                category=concept['category'],
                description=concept['description']
            )
            for concept in raw_concepts
        ]
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Create metadata
        metadata = {}
        if request.include_metadata:
            metadata = {
                "input_length": len(request.input_text),
                "extraction_method": "llm_based",
                "model_used": concept_extractor.client.default_model,
                "concept_categories": list(set([c.category for c in concepts])),
                "average_relevance": sum([c.relevance for c in concepts]) / len(concepts) if concepts else 0,
                "high_relevance_count": len([c for c in concepts if c.relevance >= 8]),
                "extraction_timestamp": start_time.isoformat()
            }
        
        logger.info(f"✅ Extracted {len(concepts)} concepts in {processing_time:.2f}s")
        
        return ExtractionResponse(
            status="success",
            concepts=concepts,
            extraction_metadata=metadata,
            processing_time_seconds=processing_time,
            total_concepts_extracted=len(concepts)
        )
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"❌ Concept extraction failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Concept extraction failed",
                "message": str(e),
                "processing_time": processing_time
            }
        )

@router.post("/extract-from-file")
async def extract_from_file(file: UploadFile = File(...), max_concepts: int = 30):
    """
    Step 1-2: Extract concepts from uploaded file
    
    Supports text files, PDFs, and documents
    """
    try:
        logger.info(f"📄 Processing uploaded file: {file.filename}")
        
        # Read file content
        content = await file.read()
        
        # Handle different file types
        if file.filename.endswith('.txt'):
            text_content = content.decode('utf-8')
        elif file.filename.endswith('.pdf'):
            # For PDF processing, you'd use a library like PyPDF2 or pdfplumber
            # For now, assume it's converted to text
            text_content = content.decode('utf-8', errors='ignore')
        else:
            # Try to decode as text
            text_content = content.decode('utf-8', errors='ignore')
        
        if len(text_content.strip()) < 10:
            raise HTTPException(
                status_code=400, 
                detail="File content too short for concept extraction"
            )
        
        # Use the same extraction logic
        request = ExtractionRequest(
            input_text=text_content,
            max_concepts=max_concepts,
            include_metadata=True
        )
        
        result = await extract_concepts(request)
        
        # Add file metadata
        if result.extraction_metadata:
            result.extraction_metadata.update({
                "source_file": file.filename,
                "file_size_bytes": len(content),
                "file_type": file.content_type or "text/plain"
            })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ File processing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"File processing failed: {str(e)}"
        )

@router.get("/health")
async def extraction_health():
    """Health check for extraction service"""
    try:
        is_healthy = await concept_extractor.client.check_health()
        
        return {
            "status": "healthy" if is_healthy else "degraded",
            "service": "concept_extraction",
            "model": concept_extractor.client.default_model,
            "ollama_connected": is_healthy,
            "capabilities": [
                "Text concept extraction",
                "File upload processing",
                "Multi-format support",
                "Metadata generation"
            ]
        }
    except Exception as e:
        logger.error(f"Extraction health check failed: {e}")
        raise HTTPException(status_code=503, detail="Extraction service unavailable")

# Utility endpoints for development and testing

@router.post("/preview-concepts")
async def preview_concepts(input_text: str, max_concepts: int = 10):
    """
    Quick preview of concept extraction (for UI development)
    Returns top concepts without full processing
    """
    try:
        if len(input_text.strip()) < 10:
            return {
                "status": "insufficient_text",
                "concepts": [],
                "message": "Provide more text for meaningful concept extraction"
            }
        
        # Extract limited concepts for preview
        raw_concepts = await concept_extractor.extract_from_text(
            input_text=input_text[:1000],  # Limit text for quick preview
            max_concepts=min(max_concepts, 10)
        )
        
        # Return simplified format
        preview_concepts = [
            {
                "name": concept['name'],
                "relevance": concept['relevance']
            }
            for concept in raw_concepts[:max_concepts]
        ]
        
        return {
            "status": "success",
            "concepts": preview_concepts,
            "total_found": len(preview_concepts),
            "is_preview": True
        }
        
    except Exception as e:
        logger.warning(f"Preview extraction failed: {e}")
        return {
            "status": "error",
            "concepts": [],
            "message": "Preview extraction failed"
        }