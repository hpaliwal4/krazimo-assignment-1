"""
Architecture Analyzer Tool.

Analyzes system architecture, design patterns, SOLID principles,
and overall structural design of the codebase.
"""

from typing import Dict, List, Any
from .base_tool import BaseTool
from ..services.ai_agent import AnalysisResult, AnalysisStatus, SeverityLevel, AgentContext


class ArchitectureAnalyzer(BaseTool):
    """
    Architecture analysis tool for design and structural assessment.
    
    Analyzes:
    - Design patterns usage
    - SOLID principles adherence
    - Architectural patterns
    - Module coupling and cohesion
    - Separation of concerns
    - Code organization structure
    """
    
    def __init__(self):
        super().__init__(
            name="architecture_analyzer",
            description="System architecture and design pattern analysis",
            version="1.0.0"
        )
    
    async def analyze(self, context: AgentContext, config: Dict[str, Any] = None) -> AnalysisResult:
        """Perform architecture analysis on the codebase."""
        self.logger.info(f"Starting architecture analysis for task {context.task_id}")
        
        try:
            # Define search patterns for architecture analysis
            search_queries = [
                # Design patterns
                "factory pattern singleton observer",
                "strategy pattern decorator adapter",
                "model view controller mvc",
                "repository pattern service layer",
                
                # Architectural patterns
                "microservice architecture monolith",
                "dependency injection container",
                "event driven architecture messaging",
                "layered architecture separation",
                
                # Code organization
                "module structure package organization",
                "interface abstract class inheritance",
                "coupling cohesion dependency",
                "configuration settings environment"
            ]
            
            # Search for architecture-related patterns
            code_results = await self._search_code_patterns(
                context, search_queries, max_results=30
            )
            
            if not code_results:
                return self._create_result(
                    status=AnalysisStatus.COMPLETED,
                    severity=SeverityLevel.LOW,
                    title="Architecture Analysis Complete - No Issues Found",
                    description="Architecture analysis completed with no significant structural issues detected.",
                    confidence_score=0.7
                )
            
            # Analyze architectural patterns
            arch_issues = await self._analyze_architectural_patterns(code_results)
            
            # Check SOLID principles
            solid_issues = await self._check_solid_principles(code_results)
            
            # Analyze module structure
            module_issues = await self._analyze_module_structure(code_results)
            
            # Combine all findings
            all_findings = arch_issues + solid_issues + module_issues
            
            # Assess overall architecture health
            overall_severity = self._assess_architecture_severity(all_findings)
            
            # Generate architectural recommendations
            recommendations = self._generate_architecture_recommendations(all_findings)
            
            return self._create_result(
                status=AnalysisStatus.COMPLETED,
                severity=overall_severity,
                title=f"Architecture Analysis Complete - {len(all_findings)} Issues Found",
                description=f"Architecture analysis identified {len(all_findings)} structural and design issues affecting maintainability and scalability.",
                findings=all_findings,
                recommendations=recommendations,
                confidence_score=0.8,
                metadata={
                    "tool_version": self.version,
                    "architecture_breakdown": {
                        "design_issues": len(arch_issues),
                        "solid_violations": len(solid_issues),
                        "module_issues": len(module_issues)
                    }
                }
            )
            
        except Exception as e:
            self.logger.error(f"Architecture analysis failed: {e}")
            return self._create_result(
                status=AnalysisStatus.FAILED,
                severity=SeverityLevel.LOW,
                title="Architecture Analysis Failed",
                description=f"Architecture analysis encountered an error: {str(e)}",
                confidence_score=0.0,
                metadata={"error": str(e)}
            )
    
    async def _analyze_architectural_patterns(self, code_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze architectural and design patterns."""
        arch_issues = []
        
        # Analyze each code chunk for architectural patterns
        for result in code_results:
            content = result["content"]
            file_path = result["file_path"]
            
            # Check for anti-patterns
            issues = self._detect_architectural_antipatterns(content, file_path)
            arch_issues.extend(issues)
            
            # Check for design pattern opportunities
            pattern_opportunities = self._identify_pattern_opportunities(content, file_path)
            arch_issues.extend(pattern_opportunities)
        
        return arch_issues
    
    def _detect_architectural_antipatterns(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Detect architectural anti-patterns."""
        antipatterns = []
        
        # God Object/Class detection
        if "class " in content:
            lines = content.split('\n')
            class_lines = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
            method_count = content.count('def ')
            
            if class_lines > 200 or method_count > 20:
                antipatterns.append({
                    "type": "architecture_issue",
                    "pattern": "god_class",
                    "severity": "high",
                    "file": file_path,
                    "line": 1,
                    "message": f"Large class detected ({class_lines} lines, {method_count} methods) - consider breaking down",
                    "content_preview": f"Class with {class_lines} lines and {method_count} methods",
                    "metadata": {
                        "antipattern": "god_class",
                        "lines": class_lines,
                        "methods": method_count
                    }
                })
        
        # Spaghetti Code detection (high complexity indicators)
        complexity_indicators = content.count('if ') + content.count('for ') + content.count('while ')
        if complexity_indicators > 50:
            antipatterns.append({
                "type": "architecture_issue",
                "pattern": "spaghetti_code",
                "severity": "medium",
                "file": file_path,
                "line": 1,
                "message": f"High complexity code detected ({complexity_indicators} control structures)",
                "content_preview": f"Complex code with {complexity_indicators} control structures",
                "metadata": {
                    "antipattern": "spaghetti_code",
                    "complexity_score": complexity_indicators
                }
            })
        
        # Hard-coded configuration
        hardcoded_patterns = ["localhost", "127.0.0.1", "password", "secret", "api_key"]
        for pattern in hardcoded_patterns:
            if pattern in content.lower() and not any(skip in file_path.lower() for skip in ["test", "example", "config"]):
                antipatterns.append({
                    "type": "architecture_issue",
                    "pattern": "hardcoded_config",
                    "severity": "medium",
                    "file": file_path,
                    "line": self._find_line_with_text(content, pattern),
                    "message": f"Hardcoded configuration detected: {pattern}",
                    "content_preview": f"Hardcoded: {pattern}",
                    "metadata": {
                        "antipattern": "hardcoded_config",
                        "config_type": pattern
                    }
                })
                break  # Only report first occurrence
        
        return antipatterns
    
    def _identify_pattern_opportunities(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Identify opportunities to apply design patterns."""
        opportunities = []
        
        # Factory pattern opportunity
        if content.count('if ') > 5 and ('create' in content.lower() or 'new ' in content.lower()):
            opportunities.append({
                "type": "architecture_opportunity",
                "pattern": "factory_pattern_opportunity",
                "severity": "low",
                "file": file_path,
                "line": 1,
                "message": "Multiple conditional object creation - consider Factory pattern",
                "content_preview": "Multiple object creation patterns detected",
                "metadata": {
                    "pattern_opportunity": "factory",
                    "reason": "conditional_object_creation"
                }
            })
        
        # Strategy pattern opportunity
        if content.count('if ') > 3 and content.count('else') > 2:
            opportunities.append({
                "type": "architecture_opportunity",
                "pattern": "strategy_pattern_opportunity",
                "severity": "low",
                "file": file_path,
                "line": 1,
                "message": "Complex conditional logic - consider Strategy pattern",
                "content_preview": "Complex conditional structure detected",
                "metadata": {
                    "pattern_opportunity": "strategy",
                    "reason": "complex_conditionals"
                }
            })
        
        return opportunities
    
    async def _check_solid_principles(self, code_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check adherence to SOLID principles."""
        solid_issues = []
        
        for result in code_results:
            content = result["content"]
            file_path = result["file_path"]
            
            # Single Responsibility Principle
            if "class " in content:
                responsibilities = self._count_responsibilities(content)
                if responsibilities > 3:
                    solid_issues.append({
                        "type": "solid_violation",
                        "pattern": "srp_violation",
                        "severity": "medium",
                        "file": file_path,
                        "line": 1,
                        "message": f"Class appears to have {responsibilities} responsibilities - violates SRP",
                        "content_preview": f"Multiple responsibilities detected",
                        "metadata": {
                            "principle": "single_responsibility",
                            "responsibility_count": responsibilities
                        }
                    })
            
            # Open/Closed Principle
            if content.count('if isinstance(') > 2:
                solid_issues.append({
                    "type": "solid_violation",
                    "pattern": "ocp_violation",
                    "severity": "medium",
                    "file": file_path,
                    "line": self._find_line_with_text(content, "isinstance"),
                    "message": "Type checking with isinstance - consider polymorphism (OCP)",
                    "content_preview": "Type checking pattern detected",
                    "metadata": {
                        "principle": "open_closed",
                        "isinstance_count": content.count('if isinstance(')
                    }
                })
            
            # Dependency Inversion Principle
            if content.count('import ') > 10 and 'class ' in content:
                concrete_imports = len([line for line in content.split('\n') 
                                      if 'import ' in line and 'interface' not in line.lower() 
                                      and 'abc' not in line.lower()])
                if concrete_imports > 5:
                    solid_issues.append({
                        "type": "solid_violation",
                        "pattern": "dip_violation",
                        "severity": "low",
                        "file": file_path,
                        "line": 1,
                        "message": f"High coupling to concrete classes ({concrete_imports} imports) - consider abstractions",
                        "content_preview": f"{concrete_imports} concrete imports",
                        "metadata": {
                            "principle": "dependency_inversion",
                            "concrete_imports": concrete_imports
                        }
                    })
        
        return solid_issues
    
    def _count_responsibilities(self, content: str) -> int:
        """Count potential responsibilities in a class."""
        # Simple heuristic: count different types of operations
        responsibilities = 0
        
        # Data access responsibility
        if any(word in content.lower() for word in ['save', 'load', 'read', 'write', 'database']):
            responsibilities += 1
        
        # Validation responsibility
        if any(word in content.lower() for word in ['validate', 'check', 'verify']):
            responsibilities += 1
        
        # Business logic responsibility
        if any(word in content.lower() for word in ['calculate', 'process', 'compute']):
            responsibilities += 1
        
        # UI/Presentation responsibility
        if any(word in content.lower() for word in ['render', 'display', 'show', 'print']):
            responsibilities += 1
        
        # Network/Communication responsibility
        if any(word in content.lower() for word in ['send', 'receive', 'request', 'response']):
            responsibilities += 1
        
        return max(1, responsibilities)  # At least 1 responsibility
    
    async def _analyze_module_structure(self, code_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze module structure and organization."""
        module_issues = []
        
        # Analyze file organization
        file_paths = [result["file_path"] for result in code_results]
        
        # Check for deep nesting
        max_depth = max(len(path.split('/')) for path in file_paths) if file_paths else 0
        if max_depth > 6:
            module_issues.append({
                "type": "module_issue",
                "pattern": "deep_directory_nesting",
                "severity": "medium",
                "file": "project_structure",
                "line": None,
                "message": f"Deep directory nesting detected (max depth: {max_depth})",
                "content_preview": f"Directory depth: {max_depth}",
                "metadata": {
                    "structure_issue": "deep_nesting",
                    "max_depth": max_depth
                }
            })
        
        # Check for naming consistency
        naming_issues = self._check_naming_consistency(file_paths)
        module_issues.extend(naming_issues)
        
        return module_issues
    
    def _check_naming_consistency(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """Check naming consistency across modules."""
        issues = []
        
        # Check for mixed naming conventions
        snake_case_files = [f for f in file_paths if '_' in f.split('/')[-1]]
        camel_case_files = [f for f in file_paths if any(c.isupper() for c in f.split('/')[-1])]
        
        if len(snake_case_files) > 0 and len(camel_case_files) > 0:
            issues.append({
                "type": "module_issue",
                "pattern": "inconsistent_naming",
                "severity": "low",
                "file": "project_structure",
                "line": None,
                "message": f"Mixed naming conventions: {len(snake_case_files)} snake_case, {len(camel_case_files)} camelCase files",
                "content_preview": "Inconsistent file naming detected",
                "metadata": {
                    "structure_issue": "naming_inconsistency",
                    "snake_case_count": len(snake_case_files),
                    "camel_case_count": len(camel_case_files)
                }
            })
        
        return issues
    
    def _find_line_with_text(self, content: str, text: str) -> int:
        """Find line number containing specific text."""
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if text.lower() in line.lower():
                return i + 1
        return 1
    
    def _assess_architecture_severity(self, findings: List[Dict[str, Any]]) -> SeverityLevel:
        """Assess overall architecture severity."""
        if not findings:
            return SeverityLevel.LOW
        
        severity_counts = {}
        for finding in findings:
            severity = finding.get("severity", "low")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Architectural issues have compounding effects
        god_classes = len([f for f in findings if f.get("pattern") == "god_class"])
        solid_violations = len([f for f in findings if f.get("type") == "solid_violation"])
        
        if god_classes > 1 or solid_violations > 5:
            return SeverityLevel.HIGH
        elif severity_counts.get("high", 0) > 0 or severity_counts.get("medium", 0) > 3:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW
    
    def _generate_architecture_recommendations(self, findings: List[Dict[str, Any]]) -> List[str]:
        """Generate architecture-specific recommendations."""
        if not findings:
            return [
                "✅ Architecture appears well-structured",
                "🏗️ Continue following SOLID principles",
                "📐 Consider documenting architectural decisions"
            ]
        
        recommendations = []
        
        # Categorize findings
        arch_issues = [f for f in findings if f.get("type") == "architecture_issue"]
        solid_violations = [f for f in findings if f.get("type") == "solid_violation"]
        module_issues = [f for f in findings if f.get("type") == "module_issue"]
        
        # Priority recommendations
        god_classes = [f for f in findings if f.get("pattern") == "god_class"]
        if god_classes:
            recommendations.append(
                f"🎯 CRITICAL: Refactor {len(god_classes)} God classes - break into smaller, focused classes"
            )
        
        if len(solid_violations) > 3:
            recommendations.append(
                f"📐 Address {len(solid_violations)} SOLID principle violations"
            )
        
        if len(module_issues) > 2:
            recommendations.append(
                f"📁 Improve module organization: {len(module_issues)} structural issues"
            )
        
        # Pattern-specific recommendations
        patterns = [f.get("pattern", "") for f in findings]
        
        if "hardcoded_config" in patterns:
            recommendations.append("⚙️ Move hardcoded configurations to environment variables or config files")
        
        if "spaghetti_code" in patterns:
            recommendations.append("🍝 Refactor complex code into smaller, well-defined functions")
        
        if any("opportunity" in p for p in patterns):
            recommendations.append("🎨 Consider applying design patterns to improve code structure")
        
        # General architecture recommendations
        architecture_recommendations = [
            "🏗️ Document architectural decisions and design patterns used",
            "📋 Implement architectural testing and quality gates",
            "🔍 Regular architecture reviews and refactoring sessions",
            "📐 Establish coding standards and architectural guidelines",
            "🎯 Apply SOLID principles consistently across the codebase"
        ]
        
        recommendations.extend(architecture_recommendations)
        
        return recommendations[:6] 