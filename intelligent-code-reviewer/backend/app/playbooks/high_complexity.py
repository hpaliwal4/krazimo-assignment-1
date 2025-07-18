"""
High Complexity Detection Playbook.

Specialized playbook for detecting functions and methods with
excessive cyclomatic complexity, cognitive load, and maintainability issues.
"""

from typing import Dict, List, Any
from .base_playbook import BasePlaybook
from ..services.ai_agent import AnalysisResult, AnalysisStatus, SeverityLevel, AgentContext


class HighComplexityPlaybook(BasePlaybook):
    """
    Playbook for detecting high complexity functions and methods.
    
    Identifies:
    - High cyclomatic complexity (>10)
    - High cognitive complexity (>15)  
    - Deep nesting (>4 levels)
    - Long parameter lists (>5 parameters)
    - Excessively long functions (>50 lines)
    """
    
    def __init__(self):
        super().__init__(
            name="high_complexity",
            description="Detects functions and methods with excessive complexity",
            version="1.0.0"
        )
        
        self.thresholds = {
            "max_cyclomatic": 10,
            "max_cognitive": 15,
            "max_nesting": 4,
            "max_parameters": 5,
            "max_lines": 50
        }
    
    async def execute(self, context: AgentContext, config: Dict[str, Any] = None) -> AnalysisResult:
        """Execute high complexity detection analysis."""
        self.logger.info(f"Starting high complexity analysis for task {context.task_id}")
        
        try:
            if config:
                self.thresholds.update(config.get("thresholds", {}))
            
            search_queries = [
                "function method definition complex logic",
                "nested if else condition complexity",
                "for while loop iteration nested",
                "function parameters arguments many",
                "method implementation logic business"
            ]
            
            code_results = await self._search_patterns(context, search_queries, max_results=30)
            
            if not code_results:
                return self._create_result(
                    status=AnalysisStatus.COMPLETED,
                    severity=SeverityLevel.LOW,
                    title="High Complexity Analysis Complete - No Issues Found",
                    description="No high complexity functions detected.",
                    confidence_score=0.8
                )
            
            complexity_findings = []
            
            for result in code_results:
                if result["chunk_type"] in ["function", "method"] or any(keyword in result["content"] for keyword in ["def ", "function "]):
                    findings = await self._analyze_function_complexity(result)
                    complexity_findings.extend(findings)
            
            overall_severity = self._assess_complexity_severity(complexity_findings)
            recommendations = self._generate_targeted_recommendations("high_complexity", complexity_findings)
            
            return self._create_result(
                status=AnalysisStatus.COMPLETED,
                severity=overall_severity,
                title=f"High Complexity Analysis Complete - {len(complexity_findings)} Issues Found",
                description=f"Identified {len(complexity_findings)} functions with excessive complexity requiring refactoring.",
                findings=complexity_findings,
                recommendations=recommendations,
                confidence_score=0.9,
                metadata={
                    "playbook_version": self.version,
                    "thresholds_used": self.thresholds,
                    "functions_analyzed": len([r for r in code_results if r["chunk_type"] in ["function", "method"]]),
                    "high_complexity_functions": len([f for f in complexity_findings if f.get("severity") in ["high", "critical"]])
                }
            )
            
        except Exception as e:
            self.logger.error(f"High complexity analysis failed: {e}")
            return self._create_result(
                status=AnalysisStatus.FAILED,
                severity=SeverityLevel.LOW,
                title="High Complexity Analysis Failed",
                description=f"Analysis encountered an error: {str(e)}",
                confidence_score=0.0,
                metadata={"error": str(e)}
            )
    
    async def _analyze_function_complexity(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze complexity of functions in the code result."""
        findings = []
        content = result["content"]
        file_path = result["file_path"]
        
        functions = self._extract_code_elements(content, "function")
        
        for func_info in functions:
            func_name = func_info["name"]
            func_content = func_info["content"]
            
            # Calculate complexity metrics
            complexity_metrics = self._calculate_complexity_metrics(func_content)
            
            # Check for violations
            violations = self._check_complexity_violations(complexity_metrics)
            
            if violations:
                severity = self._assess_severity_from_metrics(complexity_metrics, self.thresholds)
                
                findings.append({
                    "type": "high_complexity",
                    "pattern": "complex_function",
                    "severity": severity,
                    "file": file_path,
                    "line": func_info["line_start"],
                    "function_name": func_name,
                    "message": self._generate_complexity_message(func_name, violations, complexity_metrics),
                    "content_preview": f"Function {func_name} ({complexity_metrics['lines']} lines, complexity: {complexity_metrics['cyclomatic']})",
                    "metadata": {
                        "complexity_metrics": complexity_metrics,
                        "violations": violations,
                        "refactoring_suggestions": self._generate_refactoring_suggestions(complexity_metrics)
                    }
                })
        
        return findings
    
    def _calculate_complexity_metrics(self, content: str) -> Dict[str, Any]:
        """Calculate detailed complexity metrics for a function."""
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]
        
        # Cyclomatic complexity (decision points + 1)
        decision_keywords = ['if', 'elif', 'else', 'for', 'while', 'case', 'catch', 'except', 'and', 'or']
        cyclomatic = 1 + sum(content.lower().count(keyword) for keyword in decision_keywords)
        
        # Nesting depth
        max_nesting = 0
        current_nesting = 0
        for line in lines:
            stripped = line.strip()
            if any(keyword in stripped for keyword in ['if', 'for', 'while', 'try', 'with']):
                current_nesting += 1
                max_nesting = max(max_nesting, current_nesting)
            elif stripped in ['else:', 'elif', 'except:', 'finally:'] or stripped.endswith('}'):
                current_nesting = max(0, current_nesting - 1)
        
        # Parameter count (approximation)
        def_line = next((line for line in lines if 'def ' in line or 'function ' in line), '')
        params = 0
        if '(' in def_line and ')' in def_line:
            param_section = def_line[def_line.find('('):def_line.find(')')+1]
            params = param_section.count(',') + (1 if param_section.strip('()').strip() else 0)
        
        # Cognitive complexity (approximate)
        cognitive = 0
        nesting_level = 0
        for line in lines:
            stripped = line.strip().lower()
            if any(keyword in stripped for keyword in ['if', 'for', 'while']):
                nesting_level += 1
                cognitive += nesting_level
            elif 'and' in stripped or 'or' in stripped:
                cognitive += 1
            elif any(keyword in stripped for keyword in ['break', 'continue', 'goto']):
                cognitive += 1
        
        return {
            "lines": len(non_empty_lines),
            "cyclomatic": cyclomatic,
            "cognitive": cognitive,
            "nesting_depth": max_nesting,
            "parameters": params,
            "decision_points": cyclomatic - 1
        }
    
    def _check_complexity_violations(self, metrics: Dict[str, Any]) -> List[str]:
        """Check for complexity threshold violations."""
        violations = []
        
        if metrics["cyclomatic"] > self.thresholds["max_cyclomatic"]:
            violations.append(f"High cyclomatic complexity: {metrics['cyclomatic']} > {self.thresholds['max_cyclomatic']}")
        
        if metrics["cognitive"] > self.thresholds["max_cognitive"]:
            violations.append(f"High cognitive complexity: {metrics['cognitive']} > {self.thresholds['max_cognitive']}")
        
        if metrics["nesting_depth"] > self.thresholds["max_nesting"]:
            violations.append(f"Deep nesting: {metrics['nesting_depth']} > {self.thresholds['max_nesting']}")
        
        if metrics["parameters"] > self.thresholds["max_parameters"]:
            violations.append(f"Too many parameters: {metrics['parameters']} > {self.thresholds['max_parameters']}")
        
        if metrics["lines"] > self.thresholds["max_lines"]:
            violations.append(f"Function too long: {metrics['lines']} > {self.thresholds['max_lines']}")
        
        return violations
    
    def _generate_complexity_message(self, func_name: str, violations: List[str], metrics: Dict[str, Any]) -> str:
        """Generate descriptive message for complexity finding."""
        primary = violations[0] if violations else "Complexity issues"
        message = f"High complexity function: {func_name} - {primary}"
        
        if len(violations) > 1:
            message += f" (+{len(violations)-1} other issues)"
        
        return message
    
    def _generate_refactoring_suggestions(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate specific refactoring suggestions based on metrics."""
        suggestions = []
        
        if metrics["cyclomatic"] > 15:
            suggestions.append("Extract methods to reduce cyclomatic complexity")
        
        if metrics["nesting_depth"] > 3:
            suggestions.append("Use guard clauses to reduce nesting depth")
        
        if metrics["parameters"] > 5:
            suggestions.append("Use parameter objects or configuration classes")
        
        if metrics["lines"] > 50:
            suggestions.append("Split into smaller, focused functions")
        
        if metrics["cognitive"] > 20:
            suggestions.append("Simplify conditional logic and boolean expressions")
        
        return suggestions
    
    def _assess_complexity_severity(self, findings: List[Dict[str, Any]]) -> SeverityLevel:
        """Assess overall complexity severity."""
        if not findings:
            return SeverityLevel.LOW
        
        critical_count = len([f for f in findings if f.get("severity") == "critical"])
        high_count = len([f for f in findings if f.get("severity") == "high"])
        
        if critical_count > 2:
            return SeverityLevel.CRITICAL
        elif critical_count > 0 or high_count > 3:
            return SeverityLevel.HIGH
        elif high_count > 0 or len(findings) > 5:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW 