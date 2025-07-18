"""
Dependency Analyzer Tool.

Analyzes project dependencies, imports, circular dependencies,
version conflicts, and dependency health metrics.
"""

import re
from typing import Dict, List, Any, Set, Tuple
from .base_tool import BaseTool
from ..services.ai_agent import AnalysisResult, AnalysisStatus, SeverityLevel, AgentContext


class DependencyAnalyzer(BaseTool):
    """
    Dependency analysis tool for import and dependency assessment.
    
    Analyzes:
    - Import statements and dependency structure
    - Circular dependency detection
    - Unused imports
    - External dependency usage
    - Dependency version analysis
    - Import organization and grouping
    """
    
    def __init__(self):
        super().__init__(
            name="dependency_analyzer",
            description="Comprehensive dependency and import analysis",
            version="1.0.0"
        )
    
    async def analyze(self, context: AgentContext, config: Dict[str, Any] = None) -> AnalysisResult:
        """Perform dependency analysis on the codebase."""
        self.logger.info(f"Starting dependency analysis for task {context.task_id}")
        
        try:
            # Define search patterns for dependency analysis
            search_queries = [
                # Import statements
                "import from module package library",
                "require include using namespace",
                "import export default function",
                
                # Dependency declarations
                "package.json requirements.txt setup.py",
                "dependencies devDependencies peerDependencies",
                "pip install npm install yarn add",
                
                # Internal references
                "internal module reference local import",
                "relative import absolute import",
                "circular import dependency cycle"
            ]
            
            # Search for dependency-related patterns
            code_results = await self._search_code_patterns(
                context, search_queries, max_results=30
            )
            
            if not code_results:
                return self._create_result(
                    status=AnalysisStatus.COMPLETED,
                    severity=SeverityLevel.LOW,
                    title="Dependency Analysis Complete - No Issues Found",
                    description="Dependency analysis completed with no significant issues detected.",
                    confidence_score=0.7
                )
            
            # Analyze import patterns
            import_analysis = await self._analyze_imports(code_results)
            
            # Detect potential circular dependencies
            circular_deps = await self._detect_circular_dependencies(code_results)
            
            # Analyze external dependencies
            external_deps = await self._analyze_external_dependencies(code_results)
            
            # Combine all findings
            all_findings = import_analysis + circular_deps + external_deps
            
            # Assess overall dependency health
            overall_severity = self._assess_dependency_severity(all_findings)
            
            # Generate recommendations
            recommendations = self._generate_dependency_recommendations(all_findings)
            
            return self._create_result(
                status=AnalysisStatus.COMPLETED,
                severity=overall_severity,
                title=f"Dependency Analysis Complete - {len(all_findings)} Issues Found",
                description=f"Dependency analysis identified {len(all_findings)} dependency-related issues including {len(circular_deps)} potential circular dependencies.",
                findings=all_findings,
                recommendations=recommendations,
                confidence_score=0.8,
                metadata={
                    "tool_version": self.version,
                    "analysis_breakdown": {
                        "import_issues": len(import_analysis),
                        "circular_dependencies": len(circular_deps),
                        "external_dependency_issues": len(external_deps)
                    }
                }
            )
            
        except Exception as e:
            self.logger.error(f"Dependency analysis failed: {e}")
            return self._create_result(
                status=AnalysisStatus.FAILED,
                severity=SeverityLevel.LOW,
                title="Dependency Analysis Failed",
                description=f"Dependency analysis encountered an error: {str(e)}",
                confidence_score=0.0,
                metadata={"error": str(e)}
            )
    
    async def _analyze_imports(self, code_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze import statements and patterns."""
        import_findings = []
        
        # Track imports per file
        file_imports = {}
        all_imports = set()
        
        for result in code_results:
            content = result["content"]
            file_path = result["file_path"]
            
            if file_path not in file_imports:
                file_imports[file_path] = {
                    "imports": [],
                    "unused_imports": [],
                    "wildcard_imports": []
                }
            
            # Extract import statements
            imports = self._extract_imports(content)
            file_imports[file_path]["imports"].extend(imports)
            all_imports.update(imp["module"] for imp in imports)
            
            # Check for import issues
            import_issues = self._check_import_issues(content, file_path, imports)
            import_findings.extend(import_issues)
        
        # Check for duplicate imports across files
        duplicate_issues = self._check_duplicate_imports(file_imports)
        import_findings.extend(duplicate_issues)
        
        return import_findings
    
    def _extract_imports(self, content: str) -> List[Dict[str, Any]]:
        """Extract import statements from content."""
        imports = []
        
        # Python import patterns
        python_patterns = [
            r'import\s+([a-zA-Z_][a-zA-Z0-9_\.]*)',
            r'from\s+([a-zA-Z_][a-zA-Z0-9_\.]*)\s+import\s+([a-zA-Z_*][a-zA-Z0-9_,\s]*)',
        ]
        
        # JavaScript import patterns
        js_patterns = [
            r'import\s+.*?from\s+[\'"]([^\'"]*)[\'"]\s*;?',
            r'require\s*\(\s*[\'"]([^\'"]*)[\'"]\s*\)',
            r'import\s*\(\s*[\'"]([^\'"]*)[\'"]\s*\)',
        ]
        
        all_patterns = python_patterns + js_patterns
        
        for pattern in all_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            for match in matches:
                if isinstance(match, tuple):
                    module = match[0] if match[0] else match[1]
                else:
                    module = match
                
                imports.append({
                    "module": module.strip(),
                    "type": "import",
                    "line": self._find_import_line(content, module)
                })
        
        return imports
    
    def _find_import_line(self, content: str, module: str) -> int:
        """Find the line number of an import statement."""
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if module in line and ('import' in line or 'require' in line):
                return i + 1
        return 1
    
    def _check_import_issues(self, content: str, file_path: str, imports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for various import-related issues."""
        issues = []
        
        # Check for wildcard imports
        if '*' in content:
            wildcard_matches = re.findall(r'from\s+[a-zA-Z_][a-zA-Z0-9_\.]*\s+import\s+\*', content)
            for match in wildcard_matches:
                issues.append({
                    "type": "import_issue",
                    "pattern": "wildcard_import",
                    "severity": "medium",
                    "file": file_path,
                    "line": self._find_import_line(content, match),
                    "message": "Wildcard import detected - may cause namespace pollution",
                    "content_preview": match,
                    "metadata": {"import_type": "wildcard"}
                })
        
        # Check for too many imports in one file
        if len(imports) > 20:
            issues.append({
                "type": "import_issue",
                "pattern": "excessive_imports",
                "severity": "medium",
                "file": file_path,
                "line": 1,
                "message": f"File has {len(imports)} imports - consider refactoring",
                "content_preview": f"{len(imports)} imports detected",
                "metadata": {"import_count": len(imports)}
            })
        
        # Check for potentially unused imports (simple heuristic)
        for imp in imports:
            module_name = imp["module"].split('.')[-1]
            # Simple check: if module name doesn't appear elsewhere in content
            if module_name not in content.replace(f"import {module_name}", ""):
                issues.append({
                    "type": "import_issue",
                    "pattern": "potentially_unused_import",
                    "severity": "low",
                    "file": file_path,
                    "line": imp["line"],
                    "message": f"Import '{module_name}' may be unused",
                    "content_preview": f"import {imp['module']}",
                    "metadata": {"module": imp["module"]}
                })
        
        return issues
    
    def _check_duplicate_imports(self, file_imports: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """Check for duplicate imports across files."""
        duplicate_issues = []
        
        # Count module usage across files
        module_usage = {}
        for file_path, imports_data in file_imports.items():
            for imp in imports_data["imports"]:
                module = imp["module"]
                if module not in module_usage:
                    module_usage[module] = []
                module_usage[module].append(file_path)
        
        # Find commonly imported modules
        for module, files in module_usage.items():
            if len(files) > 5:  # Module imported in many files
                duplicate_issues.append({
                    "type": "import_issue",
                    "pattern": "widely_used_import",
                    "severity": "low",
                    "file": "multiple_files",
                    "line": None,
                    "message": f"Module '{module}' is imported in {len(files)} files - consider utility wrapper",
                    "content_preview": f"import {module}",
                    "metadata": {
                        "module": module,
                        "file_count": len(files),
                        "files": files[:5]  # Show first 5 files
                    }
                })
        
        return duplicate_issues
    
    async def _detect_circular_dependencies(self, code_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect potential circular dependencies."""
        circular_findings = []
        
        # Build dependency graph
        dependency_graph = {}
        
        for result in code_results:
            file_path = result["file_path"]
            imports = self._extract_imports(result["content"])
            
            # Convert file path to module name (approximation)
            module_name = self._file_path_to_module(file_path)
            
            if module_name not in dependency_graph:
                dependency_graph[module_name] = set()
            
            # Add dependencies
            for imp in imports:
                imported_module = imp["module"]
                # Only consider internal modules (simple heuristic)
                if not self._is_external_module(imported_module):
                    dependency_graph[module_name].add(imported_module)
        
        # Detect cycles using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: str, path: List[str]) -> bool:
            if node in rec_stack:
                # Found cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                
                circular_findings.append({
                    "type": "circular_dependency",
                    "pattern": "import_cycle",
                    "severity": "high",
                    "file": "multiple_files",
                    "line": None,
                    "message": f"Circular dependency detected: {' -> '.join(cycle)}",
                    "content_preview": f"Cycle: {' -> '.join(cycle)}",
                    "metadata": {
                        "cycle": cycle,
                        "cycle_length": len(cycle) - 1
                    }
                })
                return True
            
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in dependency_graph.get(node, []):
                if has_cycle(neighbor, path + [node]):
                    return True
            
            rec_stack.remove(node)
            return False
        
        # Check each module for cycles
        for module in dependency_graph:
            if module not in visited:
                has_cycle(module, [])
        
        return circular_findings
    
    def _file_path_to_module(self, file_path: str) -> str:
        """Convert file path to module name."""
        # Remove extension and convert path separators
        module = file_path.replace('/', '.').replace('\\', '.')
        if module.endswith('.py'):
            module = module[:-3]
        elif module.endswith('.js'):
            module = module[:-3]
        elif module.endswith('.ts'):
            module = module[:-3]
        
        return module
    
    def _is_external_module(self, module: str) -> bool:
        """Check if module is external (third-party)."""
        # Simple heuristics for external modules
        external_indicators = [
            'numpy', 'pandas', 'requests', 'flask', 'django', 'react', 'vue', 'angular',
            'lodash', 'moment', 'axios', 'express', 'fastapi', 'sqlalchemy'
        ]
        
        # Check if it's a standard library or known external module
        return (
            '.' not in module or  # Standard library modules usually don't have dots
            any(ext in module.lower() for ext in external_indicators) or
            module.startswith('__')  # Python built-ins
        )
    
    async def _analyze_external_dependencies(self, code_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze external dependency usage and health."""
        external_findings = []
        
        # Look for dependency configuration files
        config_files = [
            r for r in code_results 
            if any(config in r["file_path"].lower() for config in [
                "package.json", "requirements.txt", "setup.py", "pyproject.toml",
                "composer.json", "pom.xml", "build.gradle"
            ])
        ]
        
        for config_file in config_files:
            content = config_file["content"]
            file_path = config_file["file_path"]
            
            # Analyze dependency declarations
            dep_issues = self._analyze_dependency_declarations(content, file_path)
            external_findings.extend(dep_issues)
        
        return external_findings
    
    def _analyze_dependency_declarations(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Analyze dependency declaration files."""
        issues = []
        
        # Check for version pinning issues
        if "package.json" in file_path:
            # Look for unpinned versions
            unpinned_pattern = r'"[^"]+"\s*:\s*"[\^~]'
            unpinned_matches = re.findall(unpinned_pattern, content)
            
            if len(unpinned_matches) > 5:
                issues.append({
                    "type": "dependency_issue",
                    "pattern": "unpinned_versions",
                    "severity": "medium",
                    "file": file_path,
                    "line": None,
                    "message": f"Found {len(unpinned_matches)} dependencies with unpinned versions",
                    "content_preview": "Multiple unpinned dependencies detected",
                    "metadata": {"unpinned_count": len(unpinned_matches)}
                })
        
        elif "requirements.txt" in file_path:
            # Check for unpinned Python packages
            lines = content.split('\n')
            unpinned_count = 0
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '==' not in line and '>=' not in line and '<=' not in line:
                        unpinned_count += 1
            
            if unpinned_count > 3:
                issues.append({
                    "type": "dependency_issue",
                    "pattern": "unpinned_python_versions",
                    "severity": "medium",
                    "file": file_path,
                    "line": None,
                    "message": f"Found {unpinned_count} Python packages without version pins",
                    "content_preview": f"{unpinned_count} unpinned packages",
                    "metadata": {"unpinned_count": unpinned_count}
                })
        
        # Check for large number of dependencies
        dependency_count = self._count_dependencies(content, file_path)
        if dependency_count > 50:
            issues.append({
                "type": "dependency_issue",
                "pattern": "excessive_dependencies",
                "severity": "medium",
                "file": file_path,
                "line": None,
                "message": f"Project has {dependency_count} dependencies - consider reducing",
                "content_preview": f"{dependency_count} total dependencies",
                "metadata": {"dependency_count": dependency_count}
            })
        
        return issues
    
    def _count_dependencies(self, content: str, file_path: str) -> int:
        """Count total dependencies in a configuration file."""
        if "package.json" in file_path:
            # Count JSON dependencies
            dep_sections = ["dependencies", "devDependencies", "peerDependencies"]
            total = 0
            for section in dep_sections:
                if section in content:
                    # Simple count of lines between braces after section
                    section_start = content.find(f'"{section}"')
                    if section_start != -1:
                        brace_start = content.find('{', section_start)
                        if brace_start != -1:
                            brace_end = content.find('}', brace_start)
                            if brace_end != -1:
                                section_content = content[brace_start:brace_end]
                                total += section_content.count('"') // 2
            return total
        
        elif "requirements.txt" in file_path:
            # Count non-comment lines
            lines = content.split('\n')
            return len([line for line in lines if line.strip() and not line.strip().startswith('#')])
        
        return 0
    
    def _assess_dependency_severity(self, findings: List[Dict[str, Any]]) -> SeverityLevel:
        """Assess overall dependency severity."""
        if not findings:
            return SeverityLevel.LOW
        
        severity_counts = {}
        for finding in findings:
            severity = finding.get("severity", "low")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Circular dependencies are serious
        circular_deps = len([f for f in findings if f.get("pattern") == "import_cycle"])
        
        if circular_deps > 0:
            return SeverityLevel.HIGH
        elif severity_counts.get("high", 0) > 0:
            return SeverityLevel.HIGH
        elif severity_counts.get("medium", 0) > 5 or len(findings) > 15:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW
    
    def _generate_dependency_recommendations(self, findings: List[Dict[str, Any]]) -> List[str]:
        """Generate dependency-specific recommendations."""
        if not findings:
            return [
                "✅ Dependency structure appears healthy",
                "📦 Consider using dependency management tools",
                "🔍 Regularly audit dependencies for security updates"
            ]
        
        recommendations = []
        
        # Categorize findings
        circular_deps = [f for f in findings if f.get("pattern") == "import_cycle"]
        import_issues = [f for f in findings if f.get("type") == "import_issue"]
        dep_issues = [f for f in findings if f.get("type") == "dependency_issue"]
        
        # Priority recommendations
        if circular_deps:
            recommendations.append(
                f"🔄 CRITICAL: Break {len(circular_deps)} circular dependencies immediately"
            )
        
        if len(import_issues) > 10:
            recommendations.append(
                f"📋 Clean up {len(import_issues)} import issues (unused, wildcard, excessive)"
            )
        
        if dep_issues:
            recommendations.append(
                f"📦 Address {len(dep_issues)} dependency management issues"
            )
        
        # Pattern-specific recommendations
        patterns = [f.get("pattern", "") for f in findings]
        
        if "wildcard_import" in patterns:
            recommendations.append("🎯 Replace wildcard imports with specific imports")
        
        if "unpinned_versions" in patterns:
            recommendations.append("📌 Pin dependency versions for reproducible builds")
        
        if "excessive_dependencies" in patterns:
            recommendations.append("🏗️ Consider reducing dependencies and using lighter alternatives")
        
        # General dependency recommendations
        dependency_recommendations = [
            "🔒 Use dependency lock files (package-lock.json, requirements.lock)",
            "🛡️ Regularly scan dependencies for security vulnerabilities",
            "📊 Monitor dependency health and update policies",
            "🧹 Implement automated dependency updates and testing"
        ]
        
        recommendations.extend(dependency_recommendations)
        
        return recommendations[:6] 