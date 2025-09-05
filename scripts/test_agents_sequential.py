#!/usr/bin/env python3
"""
Sequential Agent Testing Script
Tests each agent individually to avoid overwhelming the system
"""

import asyncio
import sys
import os
import time
import logging
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from agents.concept_extractor import ConceptExtractor
from agents.geographic_agent import GeographicAgent
from agents.cultural_agent import CulturalAgent
from agents.linguistic_agent import LinguisticAgent
from agents.persona_agent import PersonaAgent
from agents.domain_agent import DomainAgent
from utils.ollama_client import ollama_client

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SequentialAgentTester:
    """
    Test all agents sequentially to validate functionality
    without overwhelming the local Ollama instance
    """
    
    def __init__(self):
        self.test_input = """
        We are developing an AI-powered healthcare platform that helps doctors 
        diagnose patients more efficiently. The system uses machine learning 
        to analyze medical images, patient histories, and symptoms. It provides 
        recommendations for treatments and helps with medical documentation.
        The platform needs to comply with HIPAA regulations and work across 
        different hospitals and clinics globally.
        """
        
        self.test_concepts = [
            "Healthcare AI Platform",
            "Medical Diagnosis", 
            "Machine Learning",
            "Patient Data Analysis",
            "Treatment Recommendations",
            "Medical Documentation",
            "HIPAA Compliance",
            "Hospital Integration"
        ]
        
        self.results = {}
        
    async def run_all_tests(self):
        """Run all agent tests sequentially"""
        logger.info("🧪 Starting Sequential Agent Testing")
        logger.info(f"Test input: {self.test_input[:100]}...")
        
        start_time = time.time()
        
        try:
            # Test 1: Ollama Connection
            await self._test_ollama_connection()
            
            # Test 2: Concept Extractor
            await self._test_concept_extractor()
            
            # Test 3: Geographic Agent
            await self._test_geographic_agent()
            
            # Test 4: Cultural Agent  
            await self._test_cultural_agent()
            
            # Test 5: Linguistic Agent
            await self._test_linguistic_agent()
            
            # Test 6: Persona Agent
            await self._test_persona_agent()
            
            # Test 7: Domain Agent
            await self._test_domain_agent()
            
            # Summary
            total_time = time.time() - start_time
            await self._print_summary(total_time)
            
        except KeyboardInterrupt:
            logger.info("🛑 Testing interrupted by user")
        except Exception as e:
            logger.error(f"❌ Testing failed: {e}")
        finally:
            await self._cleanup()
    
    async def _test_ollama_connection(self):
        """Test Ollama connection and model availability"""
        logger.info("🔍 Testing Ollama connection...")
        
        try:
            is_healthy = await ollama_client.check_health()
            
            if is_healthy:
                logger.info("✅ Ollama is healthy and ready")
                self.results["ollama"] = {"status": "healthy", "model": ollama_client.default_model}
            else:
                logger.warning("⚠️ Ollama connection issues detected")
                self.results["ollama"] = {"status": "unhealthy"}
                
        except Exception as e:
            logger.error(f"❌ Ollama test failed: {e}")
            self.results["ollama"] = {"status": "error", "error": str(e)}
        
        # Wait between tests
        await asyncio.sleep(2)
    
    async def _test_concept_extractor(self):
        """Test concept extraction agent"""
        logger.info("🧠 Testing Concept Extractor...")
        
        try:
            extractor = ConceptExtractor()
            
            concepts = await extractor.extract_from_text(
                input_text=self.test_input,
                max_concepts=20
            )
            
            self.results["concept_extractor"] = {
                "status": "success",
                "concepts_extracted": len(concepts),
                "sample_concepts": [c["name"] for c in concepts[:5]],
                "categories_found": list(set(c["category"] for c in concepts))
            }
            
            logger.info(f"✅ Concept Extractor: {len(concepts)} concepts extracted")
            
            # Update test concepts for other agents
            if concepts:
                self.test_concepts = [c["name"] for c in concepts[:8]]
                
        except Exception as e:
            logger.error(f"❌ Concept Extractor failed: {e}")
            self.results["concept_extractor"] = {"status": "error", "error": str(e)}
        
        await asyncio.sleep(3)
    
    async def _test_geographic_agent(self):
        """Test geographic characterization agent"""
        logger.info("🌍 Testing Geographic Agent...")
        
        try:
            agent = GeographicAgent()
            
            suggestions = await agent.process(
                core_concepts=self.test_concepts,
                additional_context={}
            )
            
            self.results["geographic_agent"] = {
                "status": "success",
                "suggestions_count": len(suggestions),
                "sample_suggestions": suggestions[:5]
            }
            
            logger.info(f"✅ Geographic Agent: {len(suggestions)} suggestions")
            
        except Exception as e:
            logger.error(f"❌ Geographic Agent failed: {e}")
            self.results["geographic_agent"] = {"status": "error", "error": str(e)}
        
        await asyncio.sleep(3)
    
    async def _test_cultural_agent(self):
        """Test cultural characterization agent"""
        logger.info("👥 Testing Cultural Agent...")
        
        try:
            agent = CulturalAgent()
            
            # Use geographic context from previous test if available
            geographic_context = []
            if "geographic_agent" in self.results and self.results["geographic_agent"]["status"] == "success":
                geographic_context = self.results["geographic_agent"]["sample_suggestions"]
            
            suggestions = await agent.process(
                core_concepts=self.test_concepts,
                additional_context={"geographic": geographic_context}
            )
            
            self.results["cultural_agent"] = {
                "status": "success", 
                "suggestions_count": len(suggestions),
                "sample_suggestions": suggestions[:5]
            }
            
            logger.info(f"✅ Cultural Agent: {len(suggestions)} suggestions")
            
        except Exception as e:
            logger.error(f"❌ Cultural Agent failed: {e}")
            self.results["cultural_agent"] = {"status": "error", "error": str(e)}
        
        await asyncio.sleep(3)
    
    async def _test_linguistic_agent(self):
        """Test linguistic characterization agent"""
        logger.info("🗣️ Testing Linguistic Agent...")
        
        try:
            agent = LinguisticAgent()
            
            suggestions = await agent.process(
                core_concepts=self.test_concepts,
                additional_context={}
            )
            
            self.results["linguistic_agent"] = {
                "status": "success",
                "suggestions_count": len(suggestions), 
                "sample_suggestions": suggestions[:5]
            }
            
            logger.info(f"✅ Linguistic Agent: {len(suggestions)} suggestions")
            
        except Exception as e:
            logger.error(f"❌ Linguistic Agent failed: {e}")
            self.results["linguistic_agent"] = {"status": "error", "error": str(e)}
        
        await asyncio.sleep(3)
    
    async def _test_persona_agent(self):
        """Test persona characterization agent"""
        logger.info("👤 Testing Persona Agent...")
        
        try:
            agent = PersonaAgent()
            
            suggestions = await agent.process(
                core_concepts=self.test_concepts,
                additional_context={}
            )
            
            self.results["persona_agent"] = {
                "status": "success",
                "suggestions_count": len(suggestions),
                "sample_suggestions": suggestions[:5]
            }
            
            logger.info(f"✅ Persona Agent: {len(suggestions)} suggestions")
            
        except Exception as e:
            logger.error(f"❌ Persona Agent failed: {e}")
            self.results["persona_agent"] = {"status": "error", "error": str(e)}
        
        await asyncio.sleep(3)
    
    async def _test_domain_agent(self):
        """Test domain characterization agent"""
        logger.info("🔧 Testing Domain Agent...")
        
        try:
            agent = DomainAgent()
            
            suggestions = await agent.process(
                core_concepts=self.test_concepts,
                additional_context={}
            )
            
            self.results["domain_agent"] = {
                "status": "success",
                "suggestions_count": len(suggestions),
                "sample_suggestions": suggestions[:5]
            }
            
            logger.info(f"✅ Domain Agent: {len(suggestions)} suggestions")
            
        except Exception as e:
            logger.error(f"❌ Domain Agent failed: {e}")
            self.results["domain_agent"] = {"status": "error", "error": str(e)}
        
        await asyncio.sleep(2)
    
    async def _print_summary(self, total_time: float):
        """Print test summary"""
        logger.info("=" * 60)
        logger.info("🎯 SEQUENTIAL AGENT TEST SUMMARY")
        logger.info("=" * 60)
        
        successful_agents = 0
        failed_agents = 0
        
        for agent_name, result in self.results.items():
            status_emoji = "✅" if result["status"] == "success" else "❌"
            
            if result["status"] == "success":
                successful_agents += 1
                
                if "suggestions_count" in result:
                    logger.info(f"{status_emoji} {agent_name}: {result['suggestions_count']} suggestions")
                elif "concepts_extracted" in result:
                    logger.info(f"{status_emoji} {agent_name}: {result['concepts_extracted']} concepts")
                else:
                    logger.info(f"{status_emoji} {agent_name}: OK")
                    
            else:
                failed_agents += 1
                logger.info(f"{status_emoji} {agent_name}: {result.get('error', 'Unknown error')}")
        
        logger.info("-" * 60)
        logger.info(f"📊 Results: {successful_agents} successful, {failed_agents} failed")
        logger.info(f"⏱️ Total time: {total_time:.1f} seconds")
        logger.info("-" * 60)
        
        if successful_agents >= 6:  # Ollama + 5 agents
            logger.info("🎉 All agents working correctly!")
            logger.info("✅ Ready for full pipeline testing")
        elif successful_agents >= 4:
            logger.info("⚠️ Most agents working - some issues to resolve")
        else:
            logger.info("❌ Significant issues detected - check Ollama and configuration")
        
        # Show sample results
        logger.info("\n📋 SAMPLE RESULTS:")
        for agent_name, result in self.results.items():
            if result["status"] == "success" and "sample_suggestions" in result:
                logger.info(f"\n{agent_name.upper()}:")
                for suggestion in result["sample_suggestions"]:
                    logger.info(f"  • {suggestion}")
    
    async def _cleanup(self):
        """Cleanup resources"""
        try:
            await ollama_client.close()
            logger.info("🧹 Resources cleaned up")
        except:
            pass

async def main():
    """Main testing function"""
    print("🚀 Starting Sequential Agent Testing")
    print("This will test each agent individually to validate the setup")
    print("Make sure Ollama is running with: ollama serve")
    print("-" * 60)
    
    tester = SequentialAgentTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Testing failed: {e}")