#!/usr/bin/env python3
"""
Test the synthetic data platform with League of Legends gaming toxicity input
to verify it works for general-purpose domains (not just indigenous topics)
"""

import asyncio
import logging
from core.pipeline import PipelineOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_gaming_toxicity_pipeline():
    """Test the pipeline with League of Legends gaming toxicity input"""
    
    print("🎮 Testing Synthetic Data Platform with Gaming Toxicity Input")
    print("=" * 60)
    
    # Gaming toxicity input - represents South American LoL community issues
    gaming_input = """
    Toxicidad en League of Legends en comunidades sudamericanas: 
    insultos racistas y xenófobos entre jugadores de diferentes países, 
    comportamiento tóxico en partidas ranked, abandono de partidas por frustración, 
    discriminación por acento regional o nivel socioeconómico, 
    uso de términos ofensivos relacionados con género y orientación sexual,
    griefing intencional y sabotaje de partidas,
    creación de ambiente hostil para jugadores nuevos,
    normalización de lenguaje violento en chat de voz y texto.
    """
    
    print(f"📝 Input text ({len(gaming_input)} chars):")
    print(f"'{gaming_input.strip()[:200]}...'")
    print()
    
    # Initialize pipeline
    orchestrator = PipelineOrchestrator()
    
    # Run full pipeline
    try:
        print("🚀 Starting full pipeline execution...")
        result = await orchestrator.run_full_pipeline(
            input_text=gaming_input,
            format_type="sft",  # Supervised Fine-Tuning format
            samples_per_combination=2,
            max_total_samples=100
        )
        
        print("\n✅ Pipeline completed successfully!")
        print("=" * 60)
        print(f"📊 Pipeline Results:")
        print(f"   Status: {result['status']}")
        print(f"   Processing Time: {result['total_processing_time_seconds']:.2f}s")
        print(f"   Stages Completed: {result['stages_completed']}/8")
        
        # Show metadata
        metadata = result.get('pipeline_metadata', {})
        print(f"\n📈 Generation Metrics:")
        print(f"   Concepts Extracted: {metadata.get('concepts_extracted', 0)}")
        print(f"   Characterization Dimensions: {metadata.get('characterization_dimensions', 0)}")
        print(f"   Total Samples Generated: {metadata.get('total_samples_generated', 0)}")
        print(f"   Format Type: {metadata.get('format_type', 'N/A')}")
        
        # Show sample of generated data
        final_data = result.get('final_data', {})
        samples = final_data.get('data', [])
        
        if samples:
            print(f"\n🎯 Sample Generated Data (showing first 2):")
            print("-" * 50)
            for i, sample in enumerate(samples[:2]):
                print(f"\nSample {i+1}:")
                for key, value in sample.items():
                    if key in ['instruction', 'response', 'question', 'answer']:
                        print(f"  {key}: {str(value)[:100]}...")
                    elif key == 'combination_id':
                        print(f"  {key}: {value}")
        
        print(f"\n🎮 Gaming Toxicity Test: PASSED")
        print("Platform successfully generated contextual data for gaming domain!")
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        print(f"🎮 Gaming Toxicity Test: FAILED")
        raise

if __name__ == "__main__":
    asyncio.run(test_gaming_toxicity_pipeline())