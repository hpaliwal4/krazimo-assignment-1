"""
Complexity Analyzer Tool.

Measures cyclomatic complexity, cognitive load, and various complexity metrics
to identify overly complex code that may be difficult to maintain or test.
"""

import re
from typing import Dict, List, Any
from .base_tool import BaseTool
from ..services.ai_agent import AnalysisResult, AnalysisStatus, SeverityLevel, AgentContext


class ComplexityAnalyzer(BaseTool):
    """
    Complexity analysis tool for measuring code complexity metrics.
    
    Analyzes:
    - Cyclomatic complexity (decision points)
    - Cognitive complexity (human comprehension difficulty)
    - Nesting depth
    - Function/method length
    - Parameter count
    - Halstead metrics approximation
    """
    
    def __init__(self):
        super().__init__(
            name="complexity_analyzer",
            description="Comprehensive complexity analysis and metrics calculation",
            version="1.0.0"
        )
        
        # Complexity indicators for different languages
        self.decision_keywords = [
            "if", "else", "elif", "switch", "case", "while", "for", 
            "foreach", "do", "try", "catch", "finally", "and", "or", "?:"
        ]
        
        self.loop_keywords = ["for", "while", "foreach", "do"]
        self.conditional_keywords = ["if", "else", "elif", "switch", "case"]
        self.exception_keywords = ["try", "catch", "finally", "except"]
    
    async def analyze(self, context: AgentContext, config: Dict[str, Any] = None) -> AnalysisResult:
        """Perform complexity analysis on the codebase."""
        self.logger.info(f"Starting complexity analysis for task {context.task_id}")
        
        try:
            # Define search patterns for complexity analysis
            search_queries = [
                # Function and method definitions
                "function definition method class",
                "def function async lambda",
                "public private protected method",
                
                # Control flow structures
                "if else elif conditional statement",
                "for while loop iteration foreach",
                "switch case default break continue",
                "try catch except finally error",
                
                # Complex structures
                "nested loop if condition",
                "long method function lines",
                "many parameters arguments",
                "complex expression calculation",
                
                # Language-specific patterns
                "arrow function callback promise",
                "generator yield async await",
                "comprehension map filter reduce"
            ]
            
            # Search for complexity-related code patterns
            code_results = await self._search_code_patterns(
                context, search_queries, max_results=25
            )
            
            if not code_results:
                return self._create_result(
                    status=AnalysisStatus.COMPLETED,
                    severity=SeverityLevel.LOW,
                    title="Complexity Analysis Complete - No Issues Found",
                    description="Complexity analysis completed with no significant complexity issues detected.",
                    confidence_score=0.7
                )
            
            # Analyze complexity metrics for each code chunk
            complexity_findings = await self._analyze_code_complexity(code_results)
            
            # Calculate overall complexity metrics
            complexity_summary = self._calculate_complexity_summary(complexity_findings)
            
            # Assess overall complexity severity
            overall_severity = self._assess_complexity_severity(complexity_findings, complexity_summary)
            
            # Generate complexity recommendations
            recommendations = self._generate_complexity_recommendations(
                complexity_findings, complexity_summary
            )
            
            return self._create_result(
                status=AnalysisStatus.COMPLETED,
                severity=overall_severity,
                title=f"Complexity Analysis Complete - {len(complexity_findings)} Issues Found",
                description=f"Complexity analysis identified {len(complexity_findings)} high-complexity code sections. Average complexity score: {complexity_summary.get('average_complexity', 0):.1f}",
                findings=complexity_findings,
                recommendations=recommendations,
                confidence_score=0.85,
                metadata={
                    "tool_version": self.version,
                    "complexity_summary": complexity_summary,
                    "analysis_scope": {
                        "chunks_analyzed": len(code_results),
                        "high_complexity_count": len([f for f in complexity_findings if f.get("severity") in ["high", "critical"]]),
                        "average_complexity": complexity_summary.get("average_complexity", 0)
                    }
                }
            )
            
        except Exception as e:
            self.logger.error(f"Complexity analysis failed: {e}")
            return self._create_result(
                status=AnalysisStatus.FAILED,
                severity=SeverityLevel.LOW,
                title="Complexity Analysis Failed",
                description=f"Complexity analysis encountered an error: {str(e)}",
                confidence_score=0.0,
                metadata={"error": str(e)}
            )
    
    async def _analyze_code_complexity(self, code_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze complexity for each code chunk."""
        complexity_findings = []
        
        for result in code_results:
            content = result["content"]
            file_path = result["file_path"]
            chunk_type = result.get("chunk_type", "unknown")
            
            # Skip non-code chunks
            if chunk_type in ["comment", "documentation", "import"]:
                continue
            
            # Calculate various complexity metrics
            cyclomatic_complexity = self._calculate_cyclomatic_complexity(content)
            cognitive_complexity = self._calculate_cognitive_complexity(content)
            nesting_depth = self._calculate_nesting_depth(content)
            line_count = len(content.split('\n'))
            
            # Calculate additional metrics
            parameter_count = self._count_parameters(content)
            decision_points = self._count_decision_points(content)
            
            # Calculate overall complexity score
            complexity_score = self._calculate_overall_complexity_score(
                cyclomatic_complexity, cognitive_complexity, nesting_depth, 
                line_count, parameter_count
            )
            
            # Determine if this is a complex section
            if complexity_score > 15 or cyclomatic_complexity > 10 or nesting_depth > 4:
                severity = self._get_complexity_severity(complexity_score, cyclomatic_complexity, nesting_depth)
                
                complexity_findings.append({
                    "type": "complexity_issue",
                    "pattern": "high_complexity",
                    "severity": severity,
                    "file": file_path,
                    "line": result.get("metadata", {}).get("start_line", 1),
                    "message": self._generate_complexity_message(
                        complexity_score, cyclomatic_complexity, cognitive_complexity, nesting_depth
                    ),
                    "content_preview": content[:150],
                    "metadata": {
                        "complexity_metrics": {
                            "overall_score": complexity_score,
                            "cyclomatic_complexity": cyclomatic_complexity,
                            "cognitive_complexity": cognitive_complexity,
                            "nesting_depth": nesting_depth,
                            "line_count": line_count,
                            "parameter_count": parameter_count,
                            "decision_points": decision_points
                        },
                        "chunk_type": chunk_type,
                        "language": result.get("language", "unknown")
                    }
                })
        
        return complexity_findings
    
    def _calculate_cyclomatic_complexity(self, content: str) -> int:
        """Calculate approximate cyclomatic complexity."""
        # Base complexity is 1
        complexity = 1
        
        content_lower = content.lower()
        
        # Count decision points
        for keyword in self.decision_keywords:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(keyword) + r'\b'
            matches = re.findall(pattern, content_lower)
            complexity += len(matches)
        
        # Additional complexity for nested structures
        nesting_level = 0
        max_nesting = 0
        
        lines = content.split('\n')
        for line in lines:
            stripped = line.strip().lower()
            
            # Increase nesting for control structures
            if any(keyword in stripped for keyword in ["if", "for", "while", "try", "def", "class"]):
                if not stripped.startswith('#'):  # Skip comments
                    nesting_level += 1
                    max_nesting = max(max_nesting, nesting_level)
            
            # Decrease nesting for closing structures (approximation)
            if any(keyword in stripped for keyword in ["end", "}", "else:", "elif", "except:", "finally:"]):
                nesting_level = max(0, nesting_level - 1)
        
        # Add complexity for deep nesting
        if max_nesting > 3:
            complexity += max_nesting - 3
        
        return complexity
    
    def _calculate_cognitive_complexity(self, content: str) -> int:
        """Calculate approximate cognitive complexity."""
        cognitive_score = 0
        nesting_level = 0
        
        content_lower = content.lower()
        lines = content.split('\n')
        
        for line in lines:
            stripped = line.strip().lower()
            
            if not stripped or stripped.startswith('#'):
                continue
            
            # Increment nesting for control structures
            if any(keyword in stripped for keyword in ["if", "for", "while", "try"]):
                nesting_level += 1
                # Cognitive complexity increases with nesting
                cognitive_score += nesting_level
            
            # Logical operators add cognitive load
            cognitive_score += line.count('&&') + line.count('||') + line.count(' and ') + line.count(' or ')
            
            # Recursion adds cognitive load
            if 'recursion' in stripped or ('def ' in stripped and any(word in content_lower for word in ['return', 'self'])):
                cognitive_score += 1
            
            # Decrease nesting (approximation)
            if any(keyword in stripped for keyword in ["end", "}", "else:", "elif"]):
                nesting_level = max(0, nesting_level - 1)
        
        return cognitive_score
    
    def _calculate_nesting_depth(self, content: str) -> int:
        """Calculate maximum nesting depth."""
        max_depth = 0
        current_depth = 0
        
        lines = content.split('\n')
        for line in lines:
            stripped = line.strip().lower()
            
            if not stripped or stripped.startswith('#'):
                continue
            
            # Count indentation level (approximation)
            indent_level = (len(line) - len(line.lstrip())) // 4
            
            # Also check for control structures
            if any(keyword in stripped for keyword in ["if", "for", "while", "try", "def", "class"]):
                current_depth = max(current_depth, indent_level + 1)
                max_depth = max(max_depth, current_depth)
        
        return max_depth
    
    def _count_parameters(self, content: str) -> int:
        """Count function parameters (approximation)."""
        # Look for function definitions and count parameters
        function_patterns = [
            r'def\s+\w+\s*\(([^)]*)\)',  # Python
            r'function\s+\w+\s*\(([^)]*)\)',  # JavaScript
            r'\w+\s*\(([^)]*)\)\s*{',  # C-style
        ]
        
        max_params = 0
        for pattern in function_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if match.strip():
                    param_count = len([p for p in match.split(',') if p.strip()])
                    max_params = max(max_params, param_count)
        
        return max_params
    
    def _count_decision_points(self, content: str) -> int:
        """Count decision points in the code."""
        decision_count = 0
        content_lower = content.lower()
        
        for keyword in self.decision_keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            matches = re.findall(pattern, content_lower)
            decision_count += len(matches)
        
        return decision_count
    
    def _calculate_overall_complexity_score(
        self, 
        cyclomatic: int, 
        cognitive: int, 
        nesting: int, 
        lines: int, 
        params: int
    ) -> float:
        """Calculate overall complexity score."""
        # Weighted combination of metrics
        score = (
            cyclomatic * 2.0 +
            cognitive * 1.5 +
            nesting * 3.0 +
            (lines / 10) * 0.5 +
            max(0, params - 3) * 2.0
        )
        
        return round(score, 1)
    
    def _get_complexity_severity(self, score: float, cyclomatic: int, nesting: int) -> str:
        """Determine severity based on complexity metrics."""
        if score > 30 or cyclomatic > 15 or nesting > 6:
            return "critical"
        elif score > 20 or cyclomatic > 10 or nesting > 4:
            return "high"
        elif score > 15 or cyclomatic > 7 or nesting > 3:
            return "medium"
        else:
            return "low"
    
    def _generate_complexity_message(
        self, 
        score: float, 
        cyclomatic: int, 
        cognitive: int, 
        nesting: int
    ) -> str:
        """Generate human-readable complexity message."""
        issues = []
        
        if cyclomatic > 10:
            issues.append(f"high cyclomatic complexity ({cyclomatic})")
        if cognitive > 15:
            issues.append(f"high cognitive complexity ({cognitive})")
        if nesting > 4:
            issues.append(f"deep nesting ({nesting} levels)")
        
        if issues:
            return f"Complex code section with {', '.join(issues)}. Overall complexity score: {score}"
        else:
            return f"Moderately complex code section. Complexity score: {score}"
    
    def _calculate_complexity_summary(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics for complexity analysis."""
        if not findings:
            return {
                "total_complex_sections": 0,
                "average_complexity": 0,
                "max_complexity": 0,
                "high_complexity_files": []
            }
        
        complexity_scores = []
        cyclomatic_scores = []
        file_complexity = {}
        
        for finding in findings:
            metrics = finding.get("metadata", {}).get("complexity_metrics", {})
            score = metrics.get("overall_score", 0)
            cyclomatic = metrics.get("cyclomatic_complexity", 0)
            file_path = finding.get("file", "unknown")
            
            complexity_scores.append(score)
            cyclomatic_scores.append(cyclomatic)
            
            if file_path not in file_complexity:
                file_complexity[file_path] = []
            file_complexity[file_path].append(score)
        
        # Calculate file-level complexity
        file_avg_complexity = {
            file: sum(scores) / len(scores) 
            for file, scores in file_complexity.items()
        }
        
        high_complexity_files = [
            file for file, avg_score in file_avg_complexity.items() 
            if avg_score > 20
        ]
        
        return {
            "total_complex_sections": len(findings),
            "average_complexity": sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0,
            "max_complexity": max(complexity_scores) if complexity_scores else 0,
            "average_cyclomatic": sum(cyclomatic_scores) / len(cyclomatic_scores) if cyclomatic_scores else 0,
            "max_cyclomatic": max(cyclomatic_scores) if cyclomatic_scores else 0,
            "high_complexity_files": high_complexity_files,
            "file_complexity_distribution": file_avg_complexity
        }
    
    def _assess_complexity_severity(
        self, 
        findings: List[Dict[str, Any]], 
        summary: Dict[str, Any]
    ) -> SeverityLevel:
        """Assess overall complexity severity."""
        if not findings:
            return SeverityLevel.LOW
        
        avg_complexity = summary.get("average_complexity", 0)
        max_complexity = summary.get("max_complexity", 0)
        critical_count = len([f for f in findings if f.get("severity") == "critical"])
        high_count = len([f for f in findings if f.get("severity") == "high"])
        
        if critical_count > 0 or max_complexity > 40:
            return SeverityLevel.CRITICAL
        elif high_count > 3 or avg_complexity > 25:
            return SeverityLevel.HIGH
        elif high_count > 0 or avg_complexity > 15 or len(findings) > 10:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW
    
    def _generate_complexity_recommendations(
        self, 
        findings: List[Dict[str, Any]], 
        summary: Dict[str, Any]
    ) -> List[str]:
        """Generate complexity-specific recommendations."""
        if not findings:
            return [
                "✅ Code complexity is within acceptable ranges",
                "📊 Consider implementing complexity monitoring in CI/CD",
                "📚 Establish complexity thresholds for code reviews"
            ]
        
        recommendations = []
        
        avg_complexity = summary.get("average_complexity", 0)
        max_complexity = summary.get("max_complexity", 0)
        high_complexity_files = summary.get("high_complexity_files", [])
        
        # Severity-based recommendations
        if max_complexity > 40:
            recommendations.append(
                f"🚨 CRITICAL: Refactor extremely complex code (max complexity: {max_complexity:.1f})"
            )
        
        if avg_complexity > 20:
            recommendations.append(
                f"⚠️ HIGH: Overall complexity is high (average: {avg_complexity:.1f}) - consider major refactoring"
            )
        
        if high_complexity_files:
            recommendations.append(
                f"📁 Focus on {len(high_complexity_files)} files with consistently high complexity"
            )
        
        # Pattern-specific recommendations
        pattern_counts = {}
        for finding in findings:
            metrics = finding.get("metadata", {}).get("complexity_metrics", {})
            
            if metrics.get("nesting_depth", 0) > 4:
                pattern_counts["deep_nesting"] = pattern_counts.get("deep_nesting", 0) + 1
            if metrics.get("cyclomatic_complexity", 0) > 10:
                pattern_counts["high_cyclomatic"] = pattern_counts.get("high_cyclomatic", 0) + 1
            if metrics.get("parameter_count", 0) > 5:
                pattern_counts["many_parameters"] = pattern_counts.get("many_parameters", 0) + 1
        
        if pattern_counts.get("deep_nesting", 0) > 3:
            recommendations.append("🔧 Extract deeply nested code into separate functions")
        
        if pattern_counts.get("high_cyclomatic", 0) > 3:
            recommendations.append("⚡ Break down complex functions with many decision points")
        
        if pattern_counts.get("many_parameters", 0) > 2:
            recommendations.append("📦 Use parameter objects or configuration classes to reduce parameter count")
        
        # General complexity recommendations
        complexity_recommendations = [
            "🎯 Set complexity limits in code quality tools (max cyclomatic: 10, max nesting: 3)",
            "♻️ Apply refactoring patterns: Extract Method, Replace Conditional with Polymorphism",
            "🧪 Increase unit test coverage for complex functions",
            "📏 Monitor complexity trends over time with code quality dashboards"
        ]
        
        recommendations.extend(complexity_recommendations)
        
        return recommendations[:6] 