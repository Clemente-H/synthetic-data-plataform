#!/usr/bin/env python3
"""
Complete Pipeline Testing - End-to-End Test
Tests the full 8-step pipeline with real data generation
"""

import asyncio
import sys
import os
import time
import logging
import json
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from core.pipeline import PipelineOrchestrator

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_complete_pipeline():
    """Test the complete 8-step pipeline"""
    
    print("🚀 COMPLETE PIPELINE TEST")
    print("=" * 60)
    print("This will test the full 8-step synthetic data generation pipeline")
    print("Expected duration: 5-10 minutes (depending on Ollama speed)")
    print("-" * 60)
    
    # Test input - Healthcare AI Platform
    test_input = """
    We are developing an AI-powered healthcare platform that helps doctors 
    diagnose patients more efficiently. The system uses machine learning 
    algorithms to analyze medical images, patient histories, and symptoms to 
    provide accurate diagnosis recommendations.
    
    The platform integrates with existing Electronic Health Record (EHR) systems 
    and provides real-time treatment suggestions based on latest medical research 
    and best practices. It includes features for medical documentation automation, 
    drug interaction checking, and patient monitoring.
    
    Key requirements include HIPAA compliance, integration with hospital workflows, 
    support for multiple languages, and scalability across different healthcare 
    systems globally. The system must handle sensitive patient data securely 
    while providing fast, accurate medical insights to healthcare professionals.
    """
    
    print(f"📝 Test Input ({len(test_input)} chars):")
    print(test_input[:200] + "..." if len(test_input) > 200 else test_input)
    print()
    
    # Initialize pipeline
    orchestrator = PipelineOrchestrator()
    
    # Progress tracking
    progress_updates = []
    
    async def progress_callback(progress):
        progress_updates.append(progress)
        stage = progress.get('current_stage', 'unknown')
        completed = progress.get('stages_completed', 0)
        total = progress.get('total_stages', 8)
        print(f"📍 Stage: {stage} ({completed}/{total})")
    
    start_time = time.time()
    
    try:
        print("🎭 Starting complete pipeline execution...")
        print()
        
        # Run full pipeline
        result = await orchestrator.run_full_pipeline(
            input_text=test_input,
            format_type="qa",  # Q&A format for testing
            samples_per_combination=2,  # Limited samples for testing
            max_total_samples=50,  # Small limit for testing
            progress_callback=progress_callback
        )
        
        total_time = time.time() - start_time
        
        # Analyze results
        print("=" * 60)
        print("🎯 PIPELINE TEST RESULTS")
        print("=" * 60)
        
        print(f"⏱️  Total Time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
        print(f"📊 Status: {result['status']}")
        print(f"🏃 Stages: {result['stages_completed']}/8")
        
        if result['status'] == 'completed':
            print("✅ PIPELINE COMPLETED SUCCESSFULLY!")
            
            # Show metadata
            metadata = result.get('pipeline_metadata', {})
            print(f"📚 Concepts Extracted: {metadata.get('concepts_extracted', 'N/A')}")
            print(f"🌍 Dimensions Used: {metadata.get('characterization_dimensions', 'N/A')}")
            print(f"📝 Samples Generated: {metadata.get('total_samples_generated', 'N/A')}")
            print(f"📋 Format: {metadata.get('format_type', 'N/A')}")
            
            # Show sample of final data
            final_data = result.get('final_data', {})
            if final_data and 'data' in final_data:
                samples = final_data['data']
                print(f"\n📋 SAMPLE GENERATED DATA ({len(samples)} total samples):")
                print("-" * 40)
                
                for i, sample in enumerate(samples[:3]):  # Show first 3 samples
                    print(f"\nSample {i+1}:")
                    if isinstance(sample, dict):
                        for key, value in sample.items():
                            if key in ['question', 'instruction', 'text']:
                                print(f"  {key}: {str(value)[:100]}...")
                            elif key in ['answer', 'response']:
                                print(f"  {key}: {str(value)[:150]}...")
                    else:
                        print(f"  {str(sample)[:200]}...")
                    print()
                
                if len(samples) > 3:
                    print(f"... and {len(samples)-3} more samples")
        
        else:
            print("❌ PIPELINE FAILED")
            print(f"Failed at stage: {result.get('failed_at_stage', 'unknown')}")
            print(f"Error: {result.get('error', 'Unknown error')}")
            
            # Show partial results
            partial = result.get('partial_results', {})
            if partial:
                print("\n📋 PARTIAL RESULTS:")
                for stage, data in partial.items():
                    if isinstance(data, dict) and 'concepts' in data:
                        print(f"  {stage}: {len(data['concepts'])} items")
                    elif isinstance(data, dict):
                        print(f"  {stage}: {len(data)} items")
                    else:
                        print(f"  {stage}: completed")
        
        print("\n" + "=" * 60)
        
        # Stage-by-stage breakdown
        print("📋 STAGE BREAKDOWN:")
        expected_stages = [
            "input_processing", "concept_extraction", "characterization",
            "human_validation", "format_selection", "generation",
            "quality_assurance", "export"
        ]
        
        for i, stage in enumerate(expected_stages, 1):
            status = "✅" if i <= result.get('stages_completed', 0) else "⏸️"
            print(f"  {status} Step {i}: {stage.replace('_', ' ').title()}")
        
        print("\n" + "=" * 60)
        print("🎉 END-TO-END PIPELINE TEST COMPLETE")
        
        return result['status'] == 'completed'
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Pipeline test failed: {e}")
        logger.error(f"Pipeline test error: {e}", exc_info=True)
        return False

async def main():
    """Main testing function"""
    print("🧪 Starting Complete Pipeline Test")
    print("Make sure Ollama is running with: ollama serve")
    print("This test will take 5-10 minutes to complete")
    
    success = await test_complete_pipeline()
    
    if success:
        print("\n🎉 All tests passed! Ready for frontend development.")
    else:
        print("\n⚠️  Some issues detected. Check logs above.")
    
    return success

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n👋 Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Testing failed: {e}")
        sys.exit(1)