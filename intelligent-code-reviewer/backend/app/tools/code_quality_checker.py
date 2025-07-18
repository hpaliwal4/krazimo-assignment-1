"""
Code Quality Checker Tool.

Checks coding standards, best practices, style guidelines,
and general code quality metrics.
"""

from typing import Dict, List, Any
from .base_tool import BaseTool
from ..services.ai_agent import AnalysisResult, AnalysisStatus, SeverityLevel, AgentContext


class CodeQualityChecker(BaseTool):
    """
    Code quality checking tool for standards and best practices.
    
    Checks:
    - Coding style and formatting
    - Naming conventions
    - Documentation quality
    - Best practice adherence
    - Code organization
    - Error handling patterns
    """
    
    def __init__(self):
        super().__init__(
            name="code_quality_checker",
            description="Coding standards and best practices verification",
            version="1.0.0"
        )
    
    async def analyze(self, context: AgentContext, config: Dict[str, Any] = None) -> AnalysisResult:
        """Perform code quality analysis on the codebase."""
        self.logger.info(f"Starting code quality check for task {context.task_id}")
        
        try:
            # Define search patterns for quality analysis
            search_queries = [
                # Naming and style
                "variable function class naming convention",
                "camelCase snake_case PascalCase style",
                "constant variable naming uppercase",
                
                # Documentation
                "comment docstring documentation",
                "TODO FIXME NOTE comment marker",
                "inline comment block comment",
                
                # Best practices
                "error handling exception try catch",
                "logging debug print output",
                "configuration environment variable",
                
                # Code organization
                "function method class structure",
                "module organization import structure",
                "constant configuration setting"
            ]
            
            # Search for quality-related patterns
            code_results = await self._search_code_patterns(
                context, search_queries, max_results=20
            )
            
            if not code_results:
                return self._create_result(
                    status=AnalysisStatus.COMPLETED,
                    severity=SeverityLevel.LOW,
                    title="Code Quality Check Complete - No Issues Found",
                    description="Code quality analysis completed with no significant issues detected.",
                    confidence_score=0.7
                )
            
            # Analyze quality patterns
            quality_issues = await self._analyze_quality_patterns(code_results)
            
            # Check naming conventions
            naming_issues = await self._check_naming_conventions(code_results)
            
            # Check documentation quality
            doc_issues = await self._check_documentation_quality(code_results)
            
            # Combine all findings
            all_findings = quality_issues + naming_issues + doc_issues
            
            # Assess overall quality
            overall_severity = self._assess_quality_severity(all_findings)
            
            # Generate recommendations
            recommendations = self._generate_quality_recommendations(all_findings)
            
            return self._create_result(
                status=AnalysisStatus.COMPLETED,
                severity=overall_severity,
                title=f"Code Quality Check Complete - {len(all_findings)} Issues Found",
                description=f"Code quality analysis identified {len(all_findings)} quality issues across coding standards, naming, and documentation.",
                findings=all_findings,
                recommendations=recommendations,
                confidence_score=0.8,
                metadata={
                    "tool_version": self.version,
                    "quality_breakdown": {
                        "style_issues": len(quality_issues),
                        "naming_issues": len(naming_issues),
                        "documentation_issues": len(doc_issues)
                    }
                }
            )
            
        except Exception as e:
            self.logger.error(f"Code quality check failed: {e}")
            return self._create_result(
                status=AnalysisStatus.FAILED,
                severity=SeverityLevel.LOW,
                title="Code Quality Check Failed",
                description=f"Code quality analysis encountered an error: {str(e)}",
                confidence_score=0.0,
                metadata={"error": str(e)}
            )
    
    async def _analyze_quality_patterns(self, code_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze general code quality patterns."""
        quality_issues = []
        
        quality_patterns = [
            ("print(", "low", "Debug print statement found - use logging instead"),
            ("console.log", "low", "Console log found - use proper logging"),
            ("TODO", "medium", "TODO comment found - should be addressed"),
            ("FIXME", "high", "FIXME comment found - requires immediate attention"),
            ("HACK", "high", "Hack comment found - indicates technical debt"),
            ("magic number", "medium", "Magic number detected - use named constants"),
            ("global ", "medium", "Global variable usage - consider alternatives"),
            ("eval(", "critical", "eval() usage detected - security risk"),
            ("exec(", "critical", "exec() usage detected - security risk"),
        ]
        
        for result in code_results:
            content = result["content"]
            file_path = result["file_path"]
            
            for pattern, severity, message in quality_patterns:
                if pattern.lower() in content.lower():
                    # Find line numbers
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if pattern.lower() in line.lower():
                            quality_issues.append({
                                "type": "quality_issue",
                                "pattern": pattern.replace("(", "").replace(" ", "_"),
                                "severity": severity,
                                "file": file_path,
                                "line": i + 1,
                                "message": message,
                                "content_preview": line.strip()[:100],
                                "metadata": {"quality_type": "best_practice"}
                            })
                            break  # Only report first occurrence per file
        
        return quality_issues
    
    async def _check_naming_conventions(self, code_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check naming convention adherence."""
        naming_issues = []
        
        for result in code_results:
            content = result["content"]
            file_path = result["file_path"]
            language = result.get("language", "unknown")
            
            # Language-specific naming checks
            if language == "python":
                naming_issues.extend(self._check_python_naming(content, file_path))
            elif language in ["javascript", "typescript"]:
                naming_issues.extend(self._check_js_naming(content, file_path))
        
        return naming_issues
    
    def _check_python_naming(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Check Python naming conventions."""
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Check function naming (should be snake_case)
            if stripped.startswith('def '):
                func_name = stripped.split('(')[0].replace('def ', '').strip()
                if func_name and not func_name.islower() and '_' not in func_name:
                    issues.append({
                        "type": "naming_issue",
                        "pattern": "python_function_naming",
                        "severity": "low",
                        "file": file_path,
                        "line": i + 1,
                        "message": f"Function '{func_name}' should use snake_case naming",
                        "content_preview": stripped[:100],
                        "metadata": {"naming_type": "function", "suggested": "snake_case"}
                    })
            
            # Check class naming (should be PascalCase)
            if stripped.startswith('class '):
                class_name = stripped.split('(')[0].split(':')[0].replace('class ', '').strip()
                if class_name and (class_name.islower() or '_' in class_name):
                    issues.append({
                        "type": "naming_issue",
                        "pattern": "python_class_naming",
                        "severity": "medium",
                        "file": file_path,
                        "line": i + 1,
                        "message": f"Class '{class_name}' should use PascalCase naming",
                        "content_preview": stripped[:100],
                        "metadata": {"naming_type": "class", "suggested": "PascalCase"}
                    })
        
        return issues
    
    def _check_js_naming(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Check JavaScript/TypeScript naming conventions."""
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Check function naming (should be camelCase)
            if 'function ' in stripped:
                parts = stripped.split('function ')
                if len(parts) > 1:
                    func_part = parts[1].split('(')[0].strip()
                    if func_part and ('_' in func_part or func_part.isupper()):
                        issues.append({
                            "type": "naming_issue",
                            "pattern": "js_function_naming",
                            "severity": "low",
                            "file": file_path,
                            "line": i + 1,
                            "message": f"Function '{func_part}' should use camelCase naming",
                            "content_preview": stripped[:100],
                            "metadata": {"naming_type": "function", "suggested": "camelCase"}
                        })
        
        return issues
    
    async def _check_documentation_quality(self, code_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check documentation quality and completeness."""
        doc_issues = []
        
        for result in code_results:
            content = result["content"]
            file_path = result["file_path"]
            chunk_type = result.get("chunk_type", "unknown")
            
            # Check for missing docstrings in functions/classes
            if chunk_type in ["function", "class"]:
                if not self._has_documentation(content):
                    doc_issues.append({
                        "type": "documentation_issue",
                        "pattern": "missing_docstring",
                        "severity": "medium",
                        "file": file_path,
                        "line": 1,
                        "message": f"Missing documentation for {chunk_type}",
                        "content_preview": content[:100],
                        "metadata": {"doc_type": "docstring", "chunk_type": chunk_type}
                    })
            
            # Check for poor comment quality
            comment_quality = self._assess_comment_quality(content)
            if comment_quality["issues"]:
                for issue in comment_quality["issues"]:
                    doc_issues.append({
                        "type": "documentation_issue",
                        "pattern": "poor_comment_quality",
                        "severity": "low",
                        "file": file_path,
                        "line": issue.get("line", 1),
                        "message": issue["message"],
                        "content_preview": issue.get("content", ""),
                        "metadata": {"doc_type": "comment"}
                    })
        
        return doc_issues
    
    def _has_documentation(self, content: str) -> bool:
        """Check if content has documentation."""
        doc_indicators = ['"""', "'''", "/**", "/*", "//", "#"]
        return any(indicator in content for indicator in doc_indicators)
    
    def _assess_comment_quality(self, content: str) -> Dict[str, Any]:
        """Assess the quality of comments in the content."""
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Check for commented code (high ratio of code-like patterns in comments)
            if stripped.startswith('#') or stripped.startswith('//'):
                comment_text = stripped[1:].strip() if stripped.startswith('#') else stripped[2:].strip()
                
                # Simple heuristic for commented code
                code_indicators = ['=', '(', ')', '{', '}', ';', 'def ', 'function', 'if ']
                code_score = sum(1 for indicator in code_indicators if indicator in comment_text)
                
                if code_score > 2 and len(comment_text) > 20:
                    issues.append({
                        "line": i + 1,
                        "message": "Commented code detected - should be removed",
                        "content": stripped[:100]
                    })
                
                # Check for very short comments
                elif len(comment_text) < 5 and comment_text not in ['TODO', 'FIXME', 'NOTE']:
                    issues.append({
                        "line": i + 1,
                        "message": "Very short comment - consider expanding",
                        "content": stripped[:100]
                    })
        
        return {
            "total_comments": len([l for l in lines if l.strip().startswith('#') or l.strip().startswith('//')]),
            "issues": issues
        }
    
    def _assess_quality_severity(self, findings: List[Dict[str, Any]]) -> SeverityLevel:
        """Assess overall quality severity."""
        if not findings:
            return SeverityLevel.LOW
        
        severity_counts = {}
        for finding in findings:
            severity = finding.get("severity", "low")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        if severity_counts.get("critical", 0) > 0:
            return SeverityLevel.CRITICAL
        elif severity_counts.get("high", 0) > 2:
            return SeverityLevel.HIGH
        elif severity_counts.get("medium", 0) > 5 or len(findings) > 15:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW
    
    def _generate_quality_recommendations(self, findings: List[Dict[str, Any]]) -> List[str]:
        """Generate quality-specific recommendations."""
        if not findings:
            return [
                "✅ Code quality appears good",
                "📝 Continue following coding standards",
                "🔍 Consider automated quality tools"
            ]
        
        recommendations = []
        
        # Categorize findings
        quality_issues = [f for f in findings if f.get("type") == "quality_issue"]
        naming_issues = [f for f in findings if f.get("type") == "naming_issue"]
        doc_issues = [f for f in findings if f.get("type") == "documentation_issue"]
        
        # Priority recommendations
        if any(f.get("severity") == "critical" for f in findings):
            recommendations.append("🚨 CRITICAL: Address security-related code quality issues immediately")
        
        if len(doc_issues) > 5:
            recommendations.append(f"📚 Improve documentation: {len(doc_issues)} missing/poor documentation instances")
        
        if len(naming_issues) > 5:
            recommendations.append(f"🏷️ Standardize naming: {len(naming_issues)} naming convention violations")
        
        # Pattern-specific recommendations
        patterns = [f.get("pattern", "") for f in findings]
        
        if "TODO" in patterns or "FIXME" in patterns:
            recommendations.append("📝 Address TODO and FIXME comments in codebase")
        
        if "print" in patterns or "console.log" in patterns:
            recommendations.append("📊 Replace debug prints with proper logging framework")
        
        if any("naming" in p for p in patterns):
            recommendations.append("🎯 Establish and enforce consistent naming conventions")
        
        # General quality recommendations
        quality_recommendations = [
            "🔧 Set up automated code formatting (Black, Prettier, etc.)",
            "📋 Implement pre-commit hooks for quality checks",
            "🧪 Add comprehensive code documentation standards",
            "📏 Use linters and static analysis tools in CI/CD"
        ]
        
        recommendations.extend(quality_recommendations)
        
        return recommendations[:6] 