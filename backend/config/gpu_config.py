#!/usr/bin/env python3
"""
GPU Parallelization Configuration
Configurable settings for leveraging multiple H100 GPUs
"""

# GPU Configuration
MAX_PARALLEL_GPUS = 4  # Editable: 1-8 GPUs available, using 4 for balance
BATCH_SIZE_PER_GPU = 8  # Combinations per GPU batch
OLLAMA_CONCURRENT_REQUESTS = MAX_PARALLEL_GPUS * 2  # Allow some overlap

# Memory and Performance Settings
GPU_MEMORY_FRACTION = 0.8  # Reserve 20% memory buffer per GPU
GENERATION_TIMEOUT = 300  # 5 minutes per combination batch

# Pipeline Parallelization Strategy
PARALLEL_STAGES = [
    "characterization",  # Run 5 agents in parallel 
    "generation"  # Split combinations across GPUs
]

SEQUENTIAL_STAGES = [
    "concept_extraction",  # Single LLM call
    "quality_assurance"   # Sequential validation
]