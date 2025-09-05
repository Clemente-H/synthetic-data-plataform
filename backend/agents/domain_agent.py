#!/usr/bin/env python3
"""
Domain Agent - Identifies technical concepts, terminology, and specialized knowledge
"""

from typing import List, Dict, Any
import logging
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class DomainAgent(BaseAgent):
    """
    Specialized agent for domain context characterization
    Identifies technical concepts, industry-specific terminology, 
    edge cases, and specialized knowledge requirements
    """
    
    def __init__(self):
        super().__init__("domain")
    
    async def process(self, core_concepts: List[str], 
                     additional_context: Dict[str, List[str]] = None) -> List[str]:
        """
        Generate domain contexts based on core concepts
        """
        logger.info(f"Processing domain contexts for concepts: {core_concepts}")
        
        # Generate AI-powered domain suggestions
        ai_suggestions = await self._generate_suggestions(
            core_concepts, 
            additional_context,
            max_suggestions=12
        )
        
        # Add technical depth variations
        technical_depth = self._get_technical_depth_variations(core_concepts)
        
        # Add industry-specific contexts
        industry_contexts = self._get_industry_specific_contexts(core_concepts)
        
        # Combine all suggestions
        all_suggestions = ai_suggestions + technical_depth + industry_contexts
        unique_suggestions = list(dict.fromkeys(all_suggestions))
        
        # Validate and return
        validated = self.validate_suggestions(unique_suggestions)
        return validated[:15]
    
    def _get_technical_depth_variations(self, core_concepts: List[str]) -> List[str]:
        """
        Generate different levels of technical depth for domain concepts
        """
        return [
            "Basic/Introductory Level",
            "Intermediate Technical Level",
            "Advanced/Expert Level",
            "Academic/Research Level",
            "Practical/Applied Level",
            "Theoretical/Conceptual Level",
            "Implementation/Hands-on Level",
            "Strategic/High-level Overview"
        ]
    
    def _get_industry_specific_contexts(self, core_concepts: List[str]) -> List[str]:
        """
        Generate industry-specific domain contexts based on concepts
        """
        concept_text = " ".join(core_concepts).lower()
        contexts = []
        
        # Healthcare domain contexts
        if any(term in concept_text for term in ['health', 'medical', 'patient', 'clinical']):
            contexts.extend([
                "Clinical Practice Guidelines",
                "Medical Research Protocols",
                "Healthcare Compliance (HIPAA)",
                "Pharmaceutical Development",
                "Medical Device Regulations",
                "Telemedicine Standards",
                "Public Health Policy",
                "Healthcare Quality Metrics"
            ])
        
        # Technology domain contexts
        if any(term in concept_text for term in ['tech', 'software', 'ai', 'data']):
            contexts.extend([
                "Software Engineering Best Practices",
                "AI/ML Model Development",
                "Data Privacy and Security",
                "Cloud Infrastructure",
                "DevOps and CI/CD",
                "API Design and Integration",
                "Cybersecurity Frameworks",
                "Tech Standards and Protocols"
            ])
        
        # Financial services domain
        if any(term in concept_text for term in ['finance', 'banking', 'investment']):
            contexts.extend([
                "Financial Regulations (SEC, FINRA)",
                "Risk Management Frameworks",
                "Investment Analysis Methods",
                "Banking Compliance (Basel III)",
                "Fintech Innovation",
                "Cryptocurrency and DeFi",
                "Financial Reporting Standards",
                "Anti-Money Laundering (AML)"
            ])
        
        # Education domain contexts
        if any(term in concept_text for term in ['education', 'learning', 'academic']):
            contexts.extend([
                "Curriculum Design Standards",
                "Educational Assessment Methods",
                "Learning Management Systems",
                "Academic Research Methodology",
                "Student Privacy (FERPA)",
                "Accessibility Standards (ADA)",
                "Online Learning Platforms",
                "Educational Technology Integration"
            ])
        
        # Legal domain contexts
        if any(term in concept_text for term in ['legal', 'law', 'compliance']):
            contexts.extend([
                "Legal Research Methodology",
                "Case Law Analysis",
                "Regulatory Compliance",
                "Contract Law Principles",
                "Intellectual Property",
                "Data Protection Laws (GDPR)",
                "Employment Law",
                "Corporate Governance"
            ])
        
        # Manufacturing/Industrial domain
        if any(term in concept_text for term in ['manufacturing', 'industrial', 'production']):
            contexts.extend([
                "Quality Control Standards (ISO)",
                "Supply Chain Management",
                "Lean Manufacturing Principles",
                "Safety Regulations (OSHA)",
                "Environmental Compliance",
                "Industrial IoT Applications",
                "Process Optimization",
                "Six Sigma Methodologies"
            ])
        
        return contexts
    
    def _get_fallback_suggestions(self) -> List[str]:
        """
        Fallback domain suggestions covering general technical contexts
        """
        return [
            "Technical Documentation",
            "Best Practices",
            "Industry Standards",
            "Compliance Requirements",
            "Quality Assurance",
            "Risk Management",
            "Process Improvement",
            "Technical Training",
            "Implementation Guidelines",
            "Performance Metrics",
            "Security Considerations",
            "Regulatory Framework",
            "Professional Development",
            "Technical Support",
            "Innovation and R&D"
        ]