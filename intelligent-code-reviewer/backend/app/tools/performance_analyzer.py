"""
Performance Analyzer Tool.

Identifies performance bottlenecks, inefficient algorithms,
and optimization opportunities in the codebase.
"""

from typing import Dict, List, Any
from .base_tool import BaseTool
from ..services.ai_agent import AnalysisResult, AnalysisStatus, SeverityLevel, AgentContext


class PerformanceAnalyzer(BaseTool):
    """
    Performance analysis tool for bottleneck detection.
    
    Analyzes:
    - Algorithmic complexity
    - Database query efficiency
    - Memory usage patterns
    - Loop optimization opportunities
    - I/O operation efficiency
    - Caching opportunities
    """
    
    def __init__(self):
        super().__init__(
            name="performance_analyzer",
            description="Performance bottleneck detection and optimization analysis",
            version="1.0.0"
        )
    
    async def analyze(self, context: AgentContext, config: Dict[str, Any] = None) -> AnalysisResult:
        """Perform performance analysis on the codebase."""
        self.logger.info(f"Starting performance analysis for task {context.task_id}")
        
        try:
            # Define search patterns for performance analysis
            search_queries = [
                # Loops and iteration
                "for loop while iteration nested",
                "list comprehension map filter reduce",
                "recursive function recursion",
                
                # Database operations
                "database query sql select insert",
                "orm query filter join relationship",
                "n+1 query problem bulk operation",
                
                # I/O operations
                "file read write open close",
                "network request http api call",
                "cache memory storage optimization",
                
                # Data structures
                "list array dict hash performance",
                "sort search algorithm complexity",
                "memory allocation large data"
            ]
            
            # Search for performance-related patterns
            code_results = await self._search_code_patterns(
                context, search_queries, max_results=25
            )
            
            if not code_results:
                return self._create_result(
                    status=AnalysisStatus.COMPLETED,
                    severity=SeverityLevel.LOW,
                    title="Performance Analysis Complete - No Issues Found",
                    description="Performance analysis completed with no significant bottlenecks detected.",
                    confidence_score=0.7
                )
            
            # Analyze performance patterns
            perf_issues = await self._analyze_performance_patterns(code_results)
            
            # Assess overall performance impact
            overall_severity = self._assess_performance_severity(perf_issues)
            
            # Generate optimization recommendations
            recommendations = self._generate_performance_recommendations(perf_issues)
            
            return self._create_result(
                status=AnalysisStatus.COMPLETED,
                severity=overall_severity,
                title=f"Performance Analysis Complete - {len(perf_issues)} Issues Found",
                description=f"Performance analysis identified {len(perf_issues)} potential bottlenecks and optimization opportunities.",
                findings=perf_issues,
                recommendations=recommendations,
                confidence_score=0.8,
                metadata={
                    "tool_version": self.version,
                    "performance_categories": self._categorize_performance_issues(perf_issues)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Performance analysis failed: {e}")
            return self._create_result(
                status=AnalysisStatus.FAILED,
                severity=SeverityLevel.LOW,
                title="Performance Analysis Failed",
                description=f"Performance analysis encountered an error: {str(e)}",
                confidence_score=0.0,
                metadata={"error": str(e)}
            )
    
    async def _analyze_performance_patterns(self, code_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze code for performance issues."""
        perf_issues = []
        
        performance_patterns = [
            # Loop inefficiencies
            ("nested for", "medium", "Nested loops detected - consider optimization"),
            ("while True", "low", "Infinite loop pattern - ensure proper exit conditions"),
            ("for i in range(len(", "low", "Use enumerate() instead of range(len())"),
            
            # Database anti-patterns
            ("for.*query", "high", "Potential N+1 query problem in loop"),
            ("SELECT * FROM", "medium", "SELECT * query - specify needed columns"),
            ("WHERE.*LIKE '%", "medium", "Leading wildcard in LIKE query - inefficient"),
            
            # Memory inefficiencies
            ("list(map(", "low", "Consider generator expression instead of list(map())"),
            ("copy.deepcopy", "medium", "Deep copy operation - expensive for large objects"),
            (".append(.*for", "low", "List comprehension may be more efficient"),
            
            # File I/O issues
            ("open(.*for.*in", "medium", "File opened in loop - consider reading once"),
            ("json.loads(.*for", "medium", "JSON parsing in loop - consider batch processing"),
            
            # Algorithm complexity
            ("sort().*for", "medium", "Sorting in loop - consider sorting once"),
            (".find(.*for", "medium", "Linear search in loop - consider data structure optimization"),
        ]
        
        for result in code_results:
            content = result["content"]
            file_path = result["file_path"]
            
            for pattern, severity, message in performance_patterns:
                if self._pattern_matches(pattern, content):
                    # Find specific line
                    lines = content.split('\n')
                    line_num = self._find_pattern_line(pattern, lines)
                    
                    perf_issues.append({
                        "type": "performance_issue",
                        "pattern": pattern.replace(".*", "_").replace("(", "").replace(")", ""),
                        "severity": severity,
                        "file": file_path,
                        "line": line_num,
                        "message": message,
                        "content_preview": self._get_line_preview(lines, line_num),
                        "metadata": {
                            "performance_category": self._categorize_pattern(pattern),
                            "optimization_potential": severity
                        }
                    })
        
        return perf_issues
    
    def _pattern_matches(self, pattern: str, content: str) -> bool:
        """Check if pattern matches content."""
        import re
        try:
            return bool(re.search(pattern, content, re.IGNORECASE))
        except re.error:
            # Simple string matching if regex fails
            return pattern.replace(".*", "").lower() in content.lower()
    
    def _find_pattern_line(self, pattern: str, lines: List[str]) -> int:
        """Find line number where pattern occurs."""
        pattern_words = [word for word in pattern.replace(".*", " ").split() if word.isalpha()]
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if all(word.lower() in line_lower for word in pattern_words[:2]):  # Match first 2 words
                return i + 1
        return 1
    
    def _get_line_preview(self, lines: List[str], line_num: int) -> str:
        """Get preview of the line with context."""
        if 1 <= line_num <= len(lines):
            return lines[line_num - 1].strip()[:100]
        return ""
    
    def _categorize_pattern(self, pattern: str) -> str:
        """Categorize performance pattern."""
        if "for" in pattern or "while" in pattern:
            return "loop_optimization"
        elif "query" in pattern or "SELECT" in pattern:
            return "database_optimization"
        elif "file" in pattern or "json" in pattern:
            return "io_optimization"
        elif "sort" in pattern or "find" in pattern:
            return "algorithm_optimization"
        else:
            return "general_optimization"
    
    def _categorize_performance_issues(self, issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize performance issues by type."""
        categories = {}
        for issue in issues:
            category = issue.get("metadata", {}).get("performance_category", "unknown")
            categories[category] = categories.get(category, 0) + 1
        return categories
    
    def _assess_performance_severity(self, issues: List[Dict[str, Any]]) -> SeverityLevel:
        """Assess overall performance severity."""
        if not issues:
            return SeverityLevel.LOW
        
        severity_counts = {}
        for issue in issues:
            severity = issue.get("severity", "low")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Performance issues in critical paths are more serious
        high_impact_patterns = ["nested for", "for.*query", "open(.*for.*in"]
        critical_issues = [
            issue for issue in issues 
            if any(pattern in issue.get("pattern", "") for pattern in high_impact_patterns)
        ]
        
        if len(critical_issues) > 2 or severity_counts.get("high", 0) > 3:
            return SeverityLevel.HIGH
        elif severity_counts.get("medium", 0) > 5 or len(issues) > 10:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW
    
    def _generate_performance_recommendations(self, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate performance-specific recommendations."""
        if not issues:
            return [
                "✅ No significant performance issues detected",
                "📊 Consider implementing performance monitoring",
                "🚀 Regularly profile application for optimization opportunities"
            ]
        
        recommendations = []
        
        # Categorize issues
        categories = self._categorize_performance_issues(issues)
        
        # Category-specific recommendations
        if categories.get("loop_optimization", 0) > 0:
            recommendations.append(
                f"🔄 Optimize {categories['loop_optimization']} loop inefficiencies"
            )
        
        if categories.get("database_optimization", 0) > 0:
            recommendations.append(
                f"🗃️ Address {categories['database_optimization']} database query issues"
            )
        
        if categories.get("io_optimization", 0) > 0:
            recommendations.append(
                f"📁 Optimize {categories['io_optimization']} I/O operations"
            )
        
        # Pattern-specific recommendations
        patterns = [issue.get("pattern", "") for issue in issues]
        
        if any("nested" in p for p in patterns):
            recommendations.append("🎯 Reduce nested loop complexity using better algorithms")
        
        if any("query" in p for p in patterns):
            recommendations.append("💾 Implement query optimization and caching strategies")
        
        if any("sort" in p for p in patterns):
            recommendations.append("📈 Optimize sorting operations and data structure choices")
        
        # General performance recommendations
        performance_recommendations = [
            "⚡ Implement performance profiling and monitoring",
            "🚀 Add caching layers for frequently accessed data",
            "📊 Use async/await for I/O bound operations",
            "🎯 Implement lazy loading and pagination for large datasets",
            "💻 Consider using more efficient data structures",
            "🔧 Set up performance testing in CI/CD pipeline"
        ]
        
        recommendations.extend(performance_recommendations)
        
        return recommendations[:6] 