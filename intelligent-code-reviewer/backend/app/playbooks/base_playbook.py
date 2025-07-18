"""
Base Playbook Interface for Targeted Code Analysis.

This module defines the base interface that all analysis playbooks must implement
to ensure consistent behavior and integration with the AI Agent.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..services.ai_agent import AnalysisResult, AnalysisStatus, SeverityLevel, AgentContext


logger = logging.getLogger(__name__)


class BasePlaybook(ABC):
    """
    Abstract base class for all code analysis playbooks.
    
    Playbooks are specialized analysis scripts that target specific architectural
    issues, anti-patterns, or security vulnerabilities with deep, focused analysis.
    """
    
    def __init__(self, name: str, description: str, version: str = "1.0.0"):
        """Initialize the playbook."""
        self.name = name
        self.description = description
        self.version = version
        self.logger = logging.getLogger(f"playbook.{name}")
    
    @abstractmethod
    async def execute(
        self,
        context: AgentContext,
        config: Dict[str, Any] = None
    ) -> AnalysisResult:
        """
        Execute the specialized analysis playbook.
        
        Args:
            context: Analysis context with project info and vector store access
            config: Playbook-specific configuration options
            
        Returns:
            AnalysisResult with focused findings and targeted recommendations
        """
        pass
    
    def _create_result(
        self,
        status: AnalysisStatus,
        severity: SeverityLevel,
        title: str,
        description: str,
        findings: List[Dict[str, Any]] = None,
        recommendations: List[str] = None,
        confidence_score: float = 0.9,
        metadata: Dict[str, Any] = None
    ) -> AnalysisResult:
        """Helper method to create standardized AnalysisResult."""
        return AnalysisResult(
            tool_name="playbook_executor",
            playbook_name=self.name,
            status=status,
            severity=severity,
            title=title,
            description=description,
            findings=findings or [],
            recommendations=recommendations or [],
            confidence_score=confidence_score,
            execution_time=0.0,  # Will be set by the agent
            metadata=metadata or {"playbook_version": self.version}
        )
    
    async def _search_patterns(
        self,
        context: AgentContext,
        search_queries: List[str],
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for specific patterns using the vector store.
        
        Args:
            context: Analysis context
            search_queries: List of targeted search queries
            max_results: Maximum results per query
            
        Returns:
            List of search results with content and metadata
        """
        all_results = []
        
        try:
            # Access vector store through the agent context
            from ..services.vector_store import VectorStore
            vector_store = VectorStore()
            
            for query in search_queries:
                results = vector_store.search(
                    context.vector_store_collection,
                    query,
                    k=max_results
                )
                
                for result in results:
                    all_results.append({
                        "query": query,
                        "content": result["content"],
                        "metadata": result["metadata"],
                        "file_path": result["metadata"].get("file_path", "unknown"),
                        "language": result["metadata"].get("language", "unknown"),
                        "chunk_type": result["metadata"].get("chunk_type", "unknown"),
                        "start_line": result["metadata"].get("start_line", 1),
                        "end_line": result["metadata"].get("end_line", 1)
                    })
            
            self.logger.info(f"Found {len(all_results)} patterns across {len(search_queries)} queries")
            return all_results
            
        except Exception as e:
            self.logger.warning(f"Failed to search patterns: {e}")
            return []
    
    def _analyze_code_metrics(
        self,
        content: str
    ) -> Dict[str, Any]:
        """
        Analyze basic code metrics for content.
        
        Args:
            content: Code content to analyze
            
        Returns:
            Dictionary with basic metrics
        """
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        return {
            "total_lines": len(lines),
            "code_lines": len(non_empty_lines),
            "comment_lines": len([line for line in lines if line.strip().startswith('#') or line.strip().startswith('//')]),
            "blank_lines": len(lines) - len(non_empty_lines),
            "method_count": content.count('def '),
            "class_count": content.count('class '),
            "function_count": content.count('function '),
            "complexity_indicators": content.count('if ') + content.count('for ') + content.count('while '),
            "import_count": content.count('import ') + content.count('from ')
        }
    
    def _extract_code_elements(
        self,
        content: str,
        element_type: str = "class"
    ) -> List[Dict[str, Any]]:
        """
        Extract specific code elements (classes, functions, etc.) from content.
        
        Args:
            content: Code content
            element_type: Type of element to extract ('class', 'function', 'method')
            
        Returns:
            List of extracted elements with metadata
        """
        elements = []
        lines = content.split('\n')
        
        if element_type == "class":
            pattern = "class "
        elif element_type in ["function", "method"]:
            pattern = "def "
        else:
            return elements
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith(pattern):
                # Extract element name
                if element_type == "class":
                    name_part = stripped.replace('class ', '').split('(')[0].split(':')[0].strip()
                elif element_type in ["function", "method"]:
                    name_part = stripped.replace('def ', '').split('(')[0].strip()
                else:
                    continue
                
                # Calculate element size (approximate)
                element_lines = 1
                indent_level = len(line) - len(line.lstrip())
                
                # Look ahead to find element end
                for j in range(i + 1, len(lines)):
                    next_line = lines[j]
                    if next_line.strip():  # Non-empty line
                        next_indent = len(next_line) - len(next_line.lstrip())
                        if next_indent <= indent_level and not next_line.strip().startswith('#'):
                            break
                    element_lines += 1
                
                elements.append({
                    "name": name_part,
                    "type": element_type,
                    "line_start": i + 1,
                    "line_end": i + element_lines,
                    "lines": element_lines,
                    "content": '\n'.join(lines[i:i + element_lines])
                })
        
        return elements
    
    def _assess_severity_from_metrics(
        self,
        metrics: Dict[str, Any],
        thresholds: Dict[str, int]
    ) -> str:
        """
        Assess severity level based on metrics and thresholds.
        
        Args:
            metrics: Code metrics dictionary
            thresholds: Threshold values for severity assessment
            
        Returns:
            Severity level string
        """
        critical_count = 0
        high_count = 0
        medium_count = 0
        
        for metric, value in metrics.items():
            if metric in thresholds:
                threshold = thresholds[metric]
                if value > threshold * 2:
                    critical_count += 1
                elif value > threshold * 1.5:
                    high_count += 1
                elif value > threshold:
                    medium_count += 1
        
        if critical_count > 0:
            return "critical"
        elif high_count > 1:
            return "high"
        elif high_count > 0 or medium_count > 2:
            return "medium"
        else:
            return "low"
    
    def _generate_targeted_recommendations(
        self,
        playbook_type: str,
        findings: List[Dict[str, Any]],
        metrics: Dict[str, Any] = None
    ) -> List[str]:
        """Generate playbook-specific recommendations."""
        if not findings:
            return [f"✅ No {playbook_type} issues detected - code appears healthy"]
        
        recommendations = []
        
        # Add severity-based recommendations
        severity_counts = {}
        for finding in findings:
            severity = finding.get("severity", "low")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        if severity_counts.get("critical", 0) > 0:
            recommendations.append(
                f"🚨 CRITICAL: Address {severity_counts['critical']} critical {playbook_type} issues immediately"
            )
        
        if severity_counts.get("high", 0) > 0:
            recommendations.append(
                f"⚠️ HIGH: Fix {severity_counts['high']} high-priority {playbook_type} issues"
            )
        
        # Add general recommendations based on playbook type
        general_recommendations = {
            "god_class": [
                "🎯 Break large classes into smaller, single-responsibility classes",
                "📦 Extract related methods into separate service classes",
                "🔧 Apply the Single Responsibility Principle (SRP)"
            ],
            "circular_dependency": [
                "🔄 Refactor code to eliminate circular imports",
                "📐 Introduce interfaces or abstract base classes",
                "🏗️ Reorganize module structure for better separation"
            ],
            "high_complexity": [
                "⚡ Simplify complex functions using Extract Method pattern",
                "🎯 Reduce cyclomatic complexity through guard clauses",
                "🔧 Break down large methods into smaller, focused functions"
            ],
            "dependency_health": [
                "📦 Update outdated dependencies to latest stable versions",
                "🛡️ Address security vulnerabilities in dependencies",
                "🔒 Pin dependency versions for reproducible builds"
            ],
            "hardcoded_secrets": [
                "🔐 Move secrets to environment variables immediately",
                "🛡️ Use secure secret management systems",
                "🔍 Implement automated secret scanning in CI/CD"
            ],
            "idor_vulnerability": [
                "🔒 Implement proper authorization checks",
                "🛡️ Use parameterized queries and input validation",
                "🔍 Add access control verification for all object references"
            ]
        }
        
        recommendations.extend(general_recommendations.get(playbook_type, []))
        
        return recommendations[:6]  # Limit to top 6 recommendations 