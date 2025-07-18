"""
Static Analyzer Tool.

Performs comprehensive static analysis to detect code quality issues,
maintainability problems, anti-patterns, and structural issues.
"""

from typing import Dict, List, Any
from .base_tool import BaseTool
from ..services.ai_agent import AnalysisResult, AnalysisStatus, SeverityLevel, AgentContext


class StaticAnalyzer(BaseTool):
    """
    Static analysis tool for code quality and maintainability assessment.
    
    Analyzes code structure, patterns, and quality indicators to identify:
    - Code smells and anti-patterns
    - Maintainability issues
    - Structural problems
    - Documentation gaps
    - Naming convention violations
    """
    
    def __init__(self):
        super().__init__(
            name="static_analyzer",
            description="Comprehensive static analysis for code quality and maintainability",
            version="1.0.0"
        )
    
    async def analyze(self, context: AgentContext, config: Dict[str, Any] = None) -> AnalysisResult:
        """Perform static analysis on the codebase."""
        self.logger.info(f"Starting static analysis for task {context.task_id}")
        
        try:
            # Define search patterns for static analysis
            search_queries = [
                # Code structure patterns
                "class definition method function",
                "import statement module dependency",
                "variable assignment initialization",
                "function parameter return type",
                
                # Quality indicators
                "todo fixme hack note comment",
                "deprecated warning obsolete legacy",
                "magic number constant literal",
                "global variable scope static",
                
                # Anti-patterns
                "code duplication repeated similar",
                "long method function lines complex",
                "god class large class methods",
                "deep nesting if else loops",
                
                # Documentation patterns
                "docstring documentation comment",
                "type annotation hint typing",
                "missing documentation undocumented"
            ]
            
            # Search for code patterns
            code_results = await self._search_code_patterns(
                context, search_queries, max_results=15
            )
            
            if not code_results:
                return self._create_result(
                    status=AnalysisStatus.COMPLETED,
                    severity=SeverityLevel.LOW,
                    title="Static Analysis Complete - No Issues Found",
                    description="Static analysis completed successfully with no significant issues detected.",
                    confidence_score=0.7
                )
            
            # Analyze complexity metrics
            complexity_metrics = self._analyze_complexity_indicators(code_results)
            
            # Define quality issue patterns
            quality_patterns = [
                # Code smells
                "TODO", "FIXME", "HACK", "XXX", "NOTE",
                "deprecated", "obsolete", "legacy",
                "magic number", "hardcoded",
                
                # Structural issues
                "god class", "long method", "long parameter list",
                "duplicate code", "dead code", "unused",
                "global variable", "singleton abuse",
                
                # Naming issues
                "bad naming", "unclear name", "abbreviation",
                "meaningless name", "misleading name",
                
                # Documentation issues
                "missing docstring", "undocumented", "no comments",
                "missing type hints", "unclear comment"
            ]
            
            # Extract quality issues
            quality_issues = self._extract_code_quality_issues(code_results, quality_patterns)
            
            # Analyze specific static analysis patterns
            static_findings = await self._analyze_static_patterns(code_results, complexity_metrics)
            
            # Combine all findings
            all_findings = quality_issues + static_findings
            
            # Assess overall severity
            overall_severity = self._assess_overall_severity(all_findings, complexity_metrics)
            
            # Generate recommendations
            recommendations = self._generate_static_analysis_recommendations(
                all_findings, complexity_metrics
            )
            
            return self._create_result(
                status=AnalysisStatus.COMPLETED,
                severity=overall_severity,
                title=f"Static Analysis Complete - {len(all_findings)} Issues Found",
                description=f"Comprehensive static analysis identified {len(all_findings)} code quality and maintainability issues across {complexity_metrics['total_files']} files.",
                findings=all_findings,
                recommendations=recommendations,
                confidence_score=0.85,
                metadata={
                    "tool_version": self.version,
                    "complexity_metrics": complexity_metrics,
                    "analysis_scope": {
                        "files_analyzed": complexity_metrics['total_files'],
                        "chunks_processed": complexity_metrics['total_chunks'],
                        "languages": complexity_metrics['languages']
                    }
                }
            )
            
        except Exception as e:
            self.logger.error(f"Static analysis failed: {e}")
            return self._create_result(
                status=AnalysisStatus.FAILED,
                severity=SeverityLevel.LOW,
                title="Static Analysis Failed",
                description=f"Static analysis encountered an error: {str(e)}",
                confidence_score=0.0,
                metadata={"error": str(e)}
            )
    
    async def _analyze_static_patterns(
        self,
        code_results: List[Dict[str, Any]],
        complexity_metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Analyze specific static analysis patterns."""
        static_findings = []
        
        # Analyze file organization
        file_patterns = complexity_metrics.get("file_patterns", {})
        if len(file_patterns) > 20:  # Too many directories
            static_findings.append({
                "type": "structural_issue",
                "pattern": "complex_file_structure",
                "severity": "medium",
                "file": "project_structure",
                "line": None,
                "message": f"Project has {len(file_patterns)} directories - consider simplifying structure",
                "metadata": {"directories": list(file_patterns.keys())[:10]}
            })
        
        # Analyze chunk distribution
        chunk_types = complexity_metrics.get("chunk_types", {})
        total_chunks = sum(chunk_types.values())
        
        if chunk_types.get("class", 0) > total_chunks * 0.6:  # Too many classes
            static_findings.append({
                "type": "architectural_issue",
                "pattern": "class_heavy_design",
                "severity": "medium",
                "file": "architecture",
                "line": None,
                "message": f"Codebase is class-heavy ({chunk_types['class']} classes vs {total_chunks} total chunks)",
                "metadata": {"class_ratio": chunk_types['class'] / total_chunks}
            })
        
        if chunk_types.get("function", 0) < total_chunks * 0.1:  # Too few functions
            static_findings.append({
                "type": "structural_issue",
                "pattern": "insufficient_modularization",
                "severity": "low",
                "file": "architecture",
                "line": None,
                "message": "Low function-to-code ratio suggests insufficient modularization",
                "metadata": {"function_ratio": chunk_types.get('function', 0) / total_chunks}
            })
        
        # Analyze language consistency
        languages = complexity_metrics.get("languages", [])
        if len(languages) > 5:  # Too many languages
            static_findings.append({
                "type": "maintenance_issue",
                "pattern": "language_proliferation",
                "severity": "medium",
                "file": "project_configuration",
                "line": None,
                "message": f"Project uses {len(languages)} programming languages - consider standardization",
                "metadata": {"languages": languages}
            })
        
        # Analyze code patterns
        for result in code_results:
            content = result["content"]
            
            # Check for long lines (approximation)
            lines = content.split("\n")
            long_lines = [i+1 for i, line in enumerate(lines) if len(line) > 120]
            if long_lines:
                static_findings.append({
                    "type": "formatting_issue",
                    "pattern": "long_lines",
                    "severity": "low",
                    "file": result["file_path"],
                    "line": long_lines[0],
                    "message": f"Found {len(long_lines)} lines exceeding 120 characters",
                    "metadata": {"long_lines": long_lines[:5]}
                })
            
            # Check for complex expressions
            complex_indicators = ["and", "or", "if", "else", "for", "while"]
            complexity_score = sum(content.lower().count(indicator) for indicator in complex_indicators)
            
            if complexity_score > 15:  # High complexity in chunk
                static_findings.append({
                    "type": "complexity_issue",
                    "pattern": "high_expression_complexity",
                    "severity": "medium",
                    "file": result["file_path"],
                    "line": None,
                    "message": f"Code chunk has high expression complexity (score: {complexity_score})",
                    "metadata": {"complexity_score": complexity_score}
                })
        
        return static_findings
    
    def _assess_overall_severity(
        self,
        findings: List[Dict[str, Any]],
        complexity_metrics: Dict[str, Any]
    ) -> SeverityLevel:
        """Assess overall severity based on findings and metrics."""
        if not findings:
            return SeverityLevel.LOW
        
        severity_counts = {}
        for finding in findings:
            severity = finding.get("severity", "low")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Determine overall severity
        if severity_counts.get("critical", 0) > 0:
            return SeverityLevel.CRITICAL
        elif severity_counts.get("high", 0) > 2:
            return SeverityLevel.HIGH
        elif severity_counts.get("medium", 0) > 5 or len(findings) > 15:
            return SeverityLevel.HIGH
        elif severity_counts.get("medium", 0) > 0 or len(findings) > 5:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW
    
    def _generate_static_analysis_recommendations(
        self,
        findings: List[Dict[str, Any]],
        complexity_metrics: Dict[str, Any]
    ) -> List[str]:
        """Generate specific recommendations for static analysis results."""
        recommendations = []
        
        if not findings:
            return [
                "✅ Code quality appears good based on static analysis",
                "📚 Consider adding more comprehensive documentation",
                "🧪 Implement automated static analysis tools in CI/CD"
            ]
        
        # Base recommendations from findings
        base_recommendations = self._generate_recommendations_from_findings(findings)
        recommendations.extend(base_recommendations[:3])
        
        # Specific static analysis recommendations
        pattern_counts = {}
        for finding in findings:
            pattern = finding.get("pattern", "unknown")
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        # Pattern-specific recommendations
        if pattern_counts.get("TODO", 0) > 5:
            recommendations.append("📝 Address the high number of TODO comments in the codebase")
        
        if pattern_counts.get("deprecated", 0) > 0:
            recommendations.append("🔄 Update deprecated APIs and methods to modern alternatives")
        
        if pattern_counts.get("complex_file_structure", 0) > 0:
            recommendations.append("📁 Simplify project structure by consolidating related modules")
        
        if pattern_counts.get("long_lines", 0) > 0:
            recommendations.append("📏 Implement consistent code formatting (max 120 chars per line)")
        
        # Complexity-based recommendations
        total_files = complexity_metrics.get("total_files", 0)
        if total_files > 50:
            recommendations.append("🏗️ Consider breaking down large modules for better maintainability")
        
        # Add static analysis specific recommendations
        static_recommendations = [
            "🔍 Integrate static analysis tools (ESLint, Pylint, SonarQube) into development workflow",
            "📋 Establish and enforce coding standards across the team",
            "🔧 Set up pre-commit hooks to catch quality issues early"
        ]
        
        recommendations.extend(static_recommendations)
        
        return recommendations[:6] 