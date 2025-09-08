#!/usr/bin/env python3
"""
Dataset Management API - List and download generated datasets
"""

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse
import os
import json
from typing import List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Use the same exports directory as the pipeline
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)  # Go up one level from api/ to backend/
EXPORTS_DIR = os.path.join(backend_dir, "exports")

@router.get("/datasets/list")
async def list_datasets() -> Dict[str, Any]:
    """List all available datasets"""
    
    if not os.path.exists(EXPORTS_DIR):
        return {
            "datasets": [],
            "total_count": 0,
            "total_size_mb": 0,
            "message": "No datasets generated yet"
        }
    
    datasets = []
    total_size = 0
    
    # Scan exports directory
    for filename in os.listdir(EXPORTS_DIR):
        if not filename.startswith('.'):  # Skip hidden files
            file_path = os.path.join(EXPORTS_DIR, filename)
            
            if os.path.isfile(file_path):
                file_size = os.path.getsize(file_path) / (1024*1024)  # MB
                total_size += file_size
                
                # Parse filename: dataset_format_timestamp_id.extension
                parts = filename.split('_')
                if len(parts) >= 4:
                    format_type = parts[1]
                    timestamp_str = parts[2]
                    pipeline_id = parts[3].split('.')[0]
                    extension = filename.split('.')[-1]
                    
                    # Parse timestamp
                    try:
                        timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                        created_at = timestamp.isoformat()
                    except:
                        created_at = "unknown"
                    
                    datasets.append({
                        "filename": filename,
                        "format_type": format_type,
                        "file_format": extension,
                        "pipeline_id": pipeline_id,
                        "size_mb": round(file_size, 2),
                        "created_at": created_at,
                        "download_url": f"/api/datasets/download/{filename}"
                    })
    
    # Sort by creation date (newest first)
    datasets.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {
        "datasets": datasets,
        "total_count": len(datasets),
        "total_size_mb": round(total_size, 2)
    }

@router.get("/datasets/download/{filename}")
async def download_dataset(filename: str):
    """Download a specific dataset file"""
    
    file_path = os.path.join(EXPORTS_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Dataset file not found")
    
    # Security check - ensure file is in exports directory
    if not os.path.abspath(file_path).startswith(os.path.abspath(EXPORTS_DIR)):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )

@router.get("/datasets/info/{filename}")
async def get_dataset_info(filename: str) -> Dict[str, Any]:
    """Get detailed information about a dataset"""
    
    file_path = os.path.join(EXPORTS_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Dataset file not found")
    
    # Security check
    if not os.path.abspath(file_path).startswith(os.path.abspath(EXPORTS_DIR)):
        raise HTTPException(status_code=403, detail="Access denied")
    
    file_info = {
        "filename": filename,
        "file_path": file_path,
        "size_mb": round(os.path.getsize(file_path) / (1024*1024), 2),
        "created_at": datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
        "modified_at": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
    }
    
    # If it's a JSON file, try to read metadata
    if filename.endswith('.json'):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'metadata' in data:
                    file_info['metadata'] = data['metadata']
                if 'samples' in data:
                    file_info['sample_count'] = len(data['samples'])
                    if data['samples']:
                        file_info['sample_preview'] = data['samples'][:3]  # First 3 samples
        except Exception as e:
            logger.warning(f"Could not read JSON metadata from {filename}: {e}")
    
    return file_info

@router.delete("/datasets/{filename}")
async def delete_dataset(filename: str) -> Dict[str, str]:
    """Delete a dataset file"""
    
    file_path = os.path.join(EXPORTS_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Dataset file not found")
    
    # Security check
    if not os.path.abspath(file_path).startswith(os.path.abspath(EXPORTS_DIR)):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        os.remove(file_path)
        return {"message": f"Dataset {filename} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete dataset: {e}")

@router.get("/datasets/stats")
async def get_datasets_stats() -> Dict[str, Any]:
    """Get overall statistics about generated datasets"""
    
    if not os.path.exists(EXPORTS_DIR):
        return {
            "total_datasets": 0,
            "total_size_mb": 0,
            "formats": {},
            "oldest_dataset": None,
            "newest_dataset": None
        }
    
    datasets = []
    total_size = 0
    formats = {}
    
    for filename in os.listdir(EXPORTS_DIR):
        if not filename.startswith('.') and os.path.isfile(os.path.join(EXPORTS_DIR, filename)):
            file_path = os.path.join(EXPORTS_DIR, filename)
            file_size = os.path.getsize(file_path) / (1024*1024)
            total_size += file_size
            
            extension = filename.split('.')[-1]
            formats[extension] = formats.get(extension, 0) + 1
            
            created_at = os.path.getctime(file_path)
            datasets.append({
                "filename": filename,
                "created_at": created_at
            })
    
    datasets.sort(key=lambda x: x["created_at"])
    
    return {
        "total_datasets": len(datasets),
        "total_size_mb": round(total_size, 2),
        "formats": formats,
        "oldest_dataset": datasets[0]["filename"] if datasets else None,
        "newest_dataset": datasets[-1]["filename"] if datasets else None
    }