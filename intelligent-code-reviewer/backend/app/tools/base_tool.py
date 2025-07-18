"""
Base Tool Interface for Code Analysis Tools.

This module defines the base interface that all analysis tools must implement
to ensure consistent behavior and integration with the AI Agent.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..services.ai_agent import AnalysisResult, AnalysisStatus, SeverityLevel, AgentContext


logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """
    Abstract base class for all code analysis tools.
    
    All analysis tools must inherit from this class and implement the analyze method.
    This ensures consistent interface and behavior across all tools.
    """
    
    def __init__(self, name: str, description: str, version: str = "1.0.0"):
        """Initialize the tool."""
        self.name = name
        self.description = description
        self.version = version
        self.logger = logging.getLogger(f"tool.{name}")
    
    @abstractmethod
    async def analyze(
        self,
        context: AgentContext,
        config: Dict[str, Any] = None
    ) -> AnalysisResult:
        """
        Perform analysis on the codebase.
        
        Args:
            context: Analysis context with project info and vector store access
            config: Tool-specific configuration options
            
        Returns:
            AnalysisResult with findings and recommendations
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
        confidence_score: float = 0.8,
        metadata: Dict[str, Any] = None
    ) -> AnalysisResult:
        """Helper method to create standardized AnalysisResult."""
        return AnalysisResult(
            tool_name=self.name,
            status=status,
            severity=severity,
            title=title,
            description=description,
            findings=findings or [],
            recommendations=recommendations or [],
            confidence_score=confidence_score,
            execution_time=0.0,  # Will be set by the agent
            metadata=metadata or {"tool_version": self.version}
        )
    
    async def _search_code_patterns(
        self,
        context: AgentContext,
        search_queries: List[str],
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for code patterns using the vector store.
        
        Args:
            context: Analysis context
            search_queries: List of search queries to execute
            max_results: Maximum results per query
            
        Returns:
            List of search results with content and metadata
        """
        all_results = []
        
        try:
            # Access vector store through the agent context
            from ..services.vector_store import VectorStoreClient
            vector_store = VectorStoreClient()
            
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
                        "chunk_type": result["metadata"].get("chunk_type", "unknown")
                    })
            
            self.logger.info(f"Found {len(all_results)} code patterns across {len(search_queries)} queries")
            return all_results
            
        except Exception as e:
            self.logger.warning(f"Failed to search code patterns: {e}")
            return []
    
    def _analyze_complexity_indicators(
        self,
        code_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze complexity indicators from code search results.
        
        Args:
            code_results: Results from code pattern search
            
        Returns:
            Dictionary with complexity metrics
        """
        complexity_metrics = {
            "total_files": len(set(r["file_path"] for r in code_results)),
            "total_chunks": len(code_results),
            "languages": list(set(r["language"] for r in code_results)),
            "chunk_types": {},
            "file_patterns": {},
            "complexity_indicators": []
        }
        
        # Count chunk types
        for result in code_results:
            chunk_type = result["chunk_type"]
            complexity_metrics["chunk_types"][chunk_type] = complexity_metrics["chunk_types"].get(chunk_type, 0) + 1
        
        # Analyze file patterns
        for result in code_results:
            file_path = result["file_path"]
            if "/" in file_path:
                directory = "/".join(file_path.split("/")[:-1])
                complexity_metrics["file_patterns"][directory] = complexity_metrics["file_patterns"].get(directory, 0) + 1
        
        # Identify complexity indicators
        high_complexity_indicators = [
            "nested loops", "multiple if statements", "long parameter list",
            "deep inheritance", "complex conditional", "switch statement",
            "try-catch block", "async await", "promise chain"
        ]
        
        for result in code_results:
            content_lower = result["content"].lower()
            for indicator in high_complexity_indicators:
                if indicator in content_lower:
                    complexity_metrics["complexity_indicators"].append({
                        "indicator": indicator,
                        "file": result["file_path"],
                        "content_preview": result["content"][:100]
                    })
        
        return complexity_metrics
    
    def _extract_code_quality_issues(
        self,
        code_results: List[Dict[str, Any]],
        quality_patterns: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Extract code quality issues from search results.
        
        Args:
            code_results: Results from code pattern search
            quality_patterns: Patterns that indicate quality issues
            
        Returns:
            List of identified quality issues
        """
        quality_issues = []
        
        for result in code_results:
            content = result["content"]
            content_lower = content.lower()
            
            for pattern in quality_patterns:
                if pattern.lower() in content_lower:
                    # Extract line information if available
                    lines = content.split("\n")
                    issue_line = None
                    for i, line in enumerate(lines):
                        if pattern.lower() in line.lower():
                            issue_line = i + 1
                            break
                    
                    quality_issues.append({
                        "type": "quality_issue",
                        "pattern": pattern,
                        "file": result["file_path"],
                        "line": issue_line,
                        "language": result["language"],
                        "content_preview": content[:150],
                        "severity": self._assess_pattern_severity(pattern),
                        "metadata": result["metadata"]
                    })
        
        return quality_issues
    
    def _assess_pattern_severity(self, pattern: str) -> str:
        """Assess the severity of a code pattern."""
        critical_patterns = [
            "sql injection", "hardcoded password", "eval(", "exec(",
            "unsafe deserialization", "command injection"
        ]
        
        high_patterns = [
            "deprecated", "todo", "fixme", "hack", "magic number",
            "global variable", "god class", "long method"
        ]
        
        medium_patterns = [
            "code duplication", "unused import", "unused variable",
            "complex condition", "nested loop"
        ]
        
        pattern_lower = pattern.lower()
        
        if any(critical in pattern_lower for critical in critical_patterns):
            return "critical"
        elif any(high in pattern_lower for high in high_patterns):
            return "high"
        elif any(medium in pattern_lower for medium in medium_patterns):
            return "medium"
        else:
            return "low"
    
    def _generate_recommendations_from_findings(
        self,
        findings: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate actionable recommendations based on findings."""
        recommendations = []
        
        if not findings:
            return ["No issues found. Code appears to be in good condition."]
        
        # Count severity levels
        severity_counts = {}
        for finding in findings:
            severity = finding.get("severity", "low")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Generate severity-based recommendations
        if severity_counts.get("critical", 0) > 0:
            recommendations.append(
                f"🚨 CRITICAL: Address {severity_counts['critical']} critical security/quality issues immediately"
            )
        
        if severity_counts.get("high", 0) > 0:
            recommendations.append(
                f"⚠️ HIGH PRIORITY: Fix {severity_counts['high']} high-severity issues"
            )
        
        # Generate pattern-specific recommendations
        patterns = [finding.get("pattern", "") for finding in findings]
        
        if any("deprecated" in p.lower() for p in patterns):
            recommendations.append("📚 Update deprecated APIs and libraries to their latest versions")
        
        if any("todo" in p.lower() or "fixme" in p.lower() for p in patterns):
            recommendations.append("📝 Address TODO and FIXME comments in the codebase")
        
        if any("duplication" in p.lower() for p in patterns):
            recommendations.append("🔄 Refactor duplicated code into reusable functions/modules")
        
        if any("complex" in p.lower() for p in patterns):
            recommendations.append("🔧 Break down complex functions into smaller, more manageable pieces")
        
        # Add general recommendations
        recommendations.extend([
            "✅ Implement automated code quality checks in CI/CD pipeline",
            "📖 Consider adding comprehensive code documentation",
            "🧪 Increase test coverage for better code reliability"
        ])
        
        return recommendations[:6]  # Limit to top 6 recommendations 