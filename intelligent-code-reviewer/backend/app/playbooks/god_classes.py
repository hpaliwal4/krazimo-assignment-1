"""
God Classes Detection Playbook.

Specialized playbook for detecting God Classes (overly large classes that
violate the Single Responsibility Principle) and related anti-patterns.
"""

from typing import Dict, List, Any
from .base_playbook import BasePlaybook
from ..services.ai_agent import AnalysisResult, AnalysisStatus, SeverityLevel, AgentContext


class GodClassesPlaybook(BasePlaybook):
    """
    Playbook for detecting God Classes and related anti-patterns.
    
    God Classes are classes that:
    - Have too many lines of code (>300 lines)
    - Have too many methods (>20 methods)
    - Have too many responsibilities
    - Violate the Single Responsibility Principle
    """
    
    def __init__(self):
        super().__init__(
            name="god_classes",
            description="Detects God Classes and Single Responsibility Principle violations",
            version="1.0.0"
        )
        
        # Thresholds for God Class detection
        self.thresholds = {
            "max_lines": 300,
            "max_methods": 20,
            "max_attributes": 15,
            "max_responsibilities": 3
        }
    
    async def execute(self, context: AgentContext, config: Dict[str, Any] = None) -> AnalysisResult:
        """Execute God Classes detection analysis."""
        self.logger.info(f"Starting God Classes analysis for task {context.task_id}")
        
        try:
            # Override thresholds if provided in config
            if config:
                self.thresholds.update(config.get("thresholds", {}))
            
            # Search for class patterns
            search_queries = [
                "class definition large method count",
                "class inheritance multiple responsibilities",
                "class methods attributes properties",
                "class implementation business logic",
                "class structure organization design"
            ]
            
            # Get class-related code chunks
            code_results = await self._search_patterns(context, search_queries, max_results=25)
            
            if not code_results:
                return self._create_result(
                    status=AnalysisStatus.COMPLETED,
                    severity=SeverityLevel.LOW,
                    title="God Classes Analysis Complete - No Issues Found",
                    description="No God Classes or SRP violations detected in the codebase.",
                    confidence_score=0.8
                )
            
            # Analyze each potential class
            god_class_findings = []
            
            for result in code_results:
                if result["chunk_type"] == "class" or "class " in result["content"]:
                    findings = await self._analyze_class_structure(result)
                    god_class_findings.extend(findings)
            
            # Assess overall severity
            overall_severity = self._assess_god_class_severity(god_class_findings)
            
            # Generate targeted recommendations
            recommendations = self._generate_targeted_recommendations(
                "god_class", god_class_findings
            )
            
            return self._create_result(
                status=AnalysisStatus.COMPLETED,
                severity=overall_severity,
                title=f"God Classes Analysis Complete - {len(god_class_findings)} Issues Found",
                description=f"Identified {len(god_class_findings)} potential God Classes and SRP violations that should be refactored for better maintainability.",
                findings=god_class_findings,
                recommendations=recommendations,
                confidence_score=0.9,
                metadata={
                    "playbook_version": self.version,
                    "thresholds_used": self.thresholds,
                    "classes_analyzed": len([r for r in code_results if r["chunk_type"] == "class"]),
                    "god_classes_found": len([f for f in god_class_findings if f.get("severity") in ["high", "critical"]])
                }
            )
            
        except Exception as e:
            self.logger.error(f"God Classes analysis failed: {e}")
            return self._create_result(
                status=AnalysisStatus.FAILED,
                severity=SeverityLevel.LOW,
                title="God Classes Analysis Failed",
                description=f"God Classes analysis encountered an error: {str(e)}",
                confidence_score=0.0,
                metadata={"error": str(e)}
            )
    
    async def _analyze_class_structure(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze a single class for God Class patterns."""
        findings = []
        content = result["content"]
        file_path = result["file_path"]
        
        # Extract class information
        classes = self._extract_code_elements(content, "class")
        
        for class_info in classes:
            class_name = class_info["name"]
            class_content = class_info["content"]
            
            # Calculate class metrics
            metrics = self._analyze_code_metrics(class_content)
            
            # Calculate additional God Class specific metrics
            god_metrics = self._calculate_god_class_metrics(class_content)
            metrics.update(god_metrics)
            
            # Check for God Class indicators
            violations = self._check_god_class_violations(metrics, class_name)
            
            if violations:
                severity = self._assess_severity_from_metrics(metrics, self.thresholds)
                
                findings.append({
                    "type": "god_class",
                    "pattern": "large_class_violation",
                    "severity": severity,
                    "file": file_path,
                    "line": class_info["line_start"],
                    "class_name": class_name,
                    "message": self._generate_god_class_message(class_name, violations, metrics),
                    "content_preview": f"Class {class_name} ({metrics['total_lines']} lines, {metrics['method_count']} methods)",
                    "metadata": {
                        "class_metrics": metrics,
                        "violations": violations,
                        "refactoring_priority": severity,
                        "suggested_split_count": self._suggest_split_count(metrics)
                    }
                })
        
        return findings
    
    def _calculate_god_class_metrics(self, content: str) -> Dict[str, Any]:
        """Calculate specific metrics for God Class detection."""
        lines = content.split('\n')
        
        # Count different types of responsibilities
        responsibilities = {
            "data_access": len([line for line in lines if any(keyword in line.lower() 
                               for keyword in ['database', 'query', 'save', 'load', 'fetch'])]),
            "business_logic": len([line for line in lines if any(keyword in line.lower() 
                                  for keyword in ['calculate', 'process', 'validate', 'compute'])]),
            "ui_presentation": len([line for line in lines if any(keyword in line.lower() 
                                   for keyword in ['render', 'display', 'show', 'print', 'format'])]),
            "network_io": len([line for line in lines if any(keyword in line.lower() 
                              for keyword in ['request', 'response', 'http', 'api', 'send'])]),
            "file_io": len([line for line in lines if any(keyword in line.lower() 
                           for keyword in ['file', 'read', 'write', 'open', 'close'])])
        }
        
        # Count attributes (approximation)
        attribute_count = len([line for line in lines if 'self.' in line and '=' in line])
        
        # Count responsibilities that are actually used
        active_responsibilities = len([resp for resp, count in responsibilities.items() if count > 0])
        
        return {
            "attribute_count": attribute_count,
            "responsibilities": responsibilities,
            "active_responsibilities": active_responsibilities,
            "coupling_indicators": content.count('import ') + content.count('from '),
            "inheritance_depth": content.count('super('),
            "method_complexity": (content.count('if ') + content.count('for ') + content.count('while ')) / max(1, content.count('def '))
        }
    
    def _check_god_class_violations(self, metrics: Dict[str, Any], class_name: str) -> List[str]:
        """Check for specific God Class violations."""
        violations = []
        
        # Size violations
        if metrics["total_lines"] > self.thresholds["max_lines"]:
            violations.append(f"Excessive lines: {metrics['total_lines']} > {self.thresholds['max_lines']}")
        
        if metrics["method_count"] > self.thresholds["max_methods"]:
            violations.append(f"Too many methods: {metrics['method_count']} > {self.thresholds['max_methods']}")
        
        if metrics["attribute_count"] > self.thresholds["max_attributes"]:
            violations.append(f"Too many attributes: {metrics['attribute_count']} > {self.thresholds['max_attributes']}")
        
        # Responsibility violations
        if metrics["active_responsibilities"] > self.thresholds["max_responsibilities"]:
            violations.append(f"Multiple responsibilities: {metrics['active_responsibilities']} > {self.thresholds['max_responsibilities']}")
        
        # Additional anti-pattern checks
        if metrics["method_complexity"] > 5:
            violations.append(f"High method complexity: {metrics['method_complexity']:.1f}")
        
        if metrics["coupling_indicators"] > 15:
            violations.append(f"High coupling: {metrics['coupling_indicators']} imports")
        
        return violations
    
    def _generate_god_class_message(self, class_name: str, violations: List[str], metrics: Dict[str, Any]) -> str:
        """Generate a descriptive message for God Class finding."""
        primary_violation = violations[0] if violations else "Multiple issues"
        
        message = f"God Class detected: {class_name} - {primary_violation}"
        
        if len(violations) > 1:
            message += f" (+{len(violations)-1} other issues)"
        
        # Add responsibility breakdown
        active_resp = [resp for resp, count in metrics["responsibilities"].items() if count > 0]
        if len(active_resp) > 1:
            message += f". Responsibilities: {', '.join(active_resp[:3])}"
        
        return message
    
    def _suggest_split_count(self, metrics: Dict[str, Any]) -> int:
        """Suggest how many classes the God Class should be split into."""
        factors = []
        
        # Based on lines
        if metrics["total_lines"] > 600:
            factors.append(metrics["total_lines"] // 300)
        
        # Based on responsibilities
        factors.append(max(2, metrics["active_responsibilities"]))
        
        # Based on method count
        if metrics["method_count"] > 30:
            factors.append(metrics["method_count"] // 15)
        
        return max(2, min(5, max(factors)))  # Between 2-5 classes
    
    def _assess_god_class_severity(self, findings: List[Dict[str, Any]]) -> SeverityLevel:
        """Assess overall God Class severity."""
        if not findings:
            return SeverityLevel.LOW
        
        critical_count = len([f for f in findings if f.get("severity") == "critical"])
        high_count = len([f for f in findings if f.get("severity") == "high"])
        
        if critical_count > 1:
            return SeverityLevel.CRITICAL
        elif critical_count > 0 or high_count > 2:
            return SeverityLevel.HIGH
        elif high_count > 0 or len(findings) > 3:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW 