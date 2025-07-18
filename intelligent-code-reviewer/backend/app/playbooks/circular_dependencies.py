"""
Circular Dependencies Detection Playbook.

Specialized playbook for detecting circular dependencies, import cycles,
and problematic dependency chains in the codebase.
"""

from typing import Dict, List, Any, Set
from .base_playbook import BasePlaybook
from ..services.ai_agent import AnalysisResult, AnalysisStatus, SeverityLevel, AgentContext


class CircularDependenciesPlaybook(BasePlaybook):
    """
    Playbook for detecting circular dependencies and import cycles.
    
    Detects:
    - Direct circular imports (A imports B, B imports A)
    - Indirect circular dependencies (A->B->C->A)
    - Problematic dependency chains
    - Module coupling issues
    """
    
    def __init__(self):
        super().__init__(
            name="circular_dependencies",
            description="Detects circular imports and dependency cycles",
            version="1.0.0"
        )
    
    async def execute(self, context: AgentContext, config: Dict[str, Any] = None) -> AnalysisResult:
        """Execute circular dependencies detection analysis."""
        self.logger.info(f"Starting circular dependencies analysis for task {context.task_id}")
        
        try:
            # Search for import and dependency patterns
            search_queries = [
                "import from module dependency",
                "circular import cycle reference",
                "module dependency relationship",
                "package import structure organization",
                "relative import absolute import"
            ]
            
            # Get import-related code chunks
            code_results = await self._search_patterns(context, search_queries, max_results=30)
            
            if not code_results:
                return self._create_result(
                    status=AnalysisStatus.COMPLETED,
                    severity=SeverityLevel.LOW,
                    title="Circular Dependencies Analysis Complete - No Issues Found",
                    description="No circular dependencies or import cycles detected.",
                    confidence_score=0.8
                )
            
            # Build dependency graph
            dependency_graph = self._build_dependency_graph(code_results)
            
            # Detect circular dependencies
            circular_deps = self._detect_cycles(dependency_graph)
            
            # Analyze dependency patterns
            dependency_issues = self._analyze_dependency_patterns(code_results, dependency_graph)
            
            # Combine findings
            all_findings = circular_deps + dependency_issues
            
            # Assess overall severity
            overall_severity = self._assess_circular_deps_severity(all_findings)
            
            # Generate recommendations
            recommendations = self._generate_targeted_recommendations(
                "circular_dependency", all_findings
            )
            
            return self._create_result(
                status=AnalysisStatus.COMPLETED,
                severity=overall_severity,
                title=f"Circular Dependencies Analysis Complete - {len(all_findings)} Issues Found",
                description=f"Detected {len(circular_deps)} circular dependencies and {len(dependency_issues)} dependency issues that need attention.",
                findings=all_findings,
                recommendations=recommendations,
                confidence_score=0.9,
                metadata={
                    "playbook_version": self.version,
                    "modules_analyzed": len(dependency_graph),
                    "circular_dependencies": len(circular_deps),
                    "dependency_issues": len(dependency_issues),
                    "max_cycle_length": max([len(f.get("metadata", {}).get("cycle", [])) for f in circular_deps], default=0)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Circular dependencies analysis failed: {e}")
            return self._create_result(
                status=AnalysisStatus.FAILED,
                severity=SeverityLevel.LOW,
                title="Circular Dependencies Analysis Failed",
                description=f"Analysis encountered an error: {str(e)}",
                confidence_score=0.0,
                metadata={"error": str(e)}
            )
    
    def _build_dependency_graph(self, code_results: List[Dict[str, Any]]) -> Dict[str, Set[str]]:
        """Build a dependency graph from import statements."""
        dependency_graph = {}
        
        for result in code_results:
            file_path = result["file_path"]
            content = result["content"]
            
            # Convert file path to module name
            module_name = self._file_path_to_module(file_path)
            
            if module_name not in dependency_graph:
                dependency_graph[module_name] = set()
            
            # Extract imports from content
            imports = self._extract_imports(content)
            
            for imported_module in imports:
                # Only consider internal modules
                if self._is_internal_module(imported_module, file_path):
                    dependency_graph[module_name].add(imported_module)
        
        return dependency_graph
    
    def _file_path_to_module(self, file_path: str) -> str:
        """Convert file path to module name."""
        # Remove common prefixes and file extensions
        module = file_path.replace('/', '.').replace('\\', '.')
        
        # Remove file extensions
        for ext in ['.py', '.js', '.ts', '.jsx', '.tsx']:
            if module.endswith(ext):
                module = module[:-len(ext)]
                break
        
        # Remove common prefixes
        for prefix in ['src.', 'app.', 'lib.']:
            if module.startswith(prefix):
                module = module[len(prefix):]
                break
        
        return module
    
    def _extract_imports(self, content: str) -> List[str]:
        """Extract import statements from content."""
        imports = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Python imports
            if line.startswith('import '):
                module = line.replace('import ', '').split(' as ')[0].split(',')[0].strip()
                imports.append(module)
            elif line.startswith('from ') and ' import ' in line:
                module = line.split(' import ')[0].replace('from ', '').strip()
                imports.append(module)
            
            # JavaScript/TypeScript imports
            elif 'import ' in line and ' from ' in line:
                parts = line.split(' from ')
                if len(parts) > 1:
                    module = parts[1].strip().strip(';').strip('\'"')
                    imports.append(module)
            elif line.startswith('const ') and 'require(' in line:
                # CommonJS require
                start = line.find("require('") or line.find('require("')
                if start != -1:
                    quote_char = line[start + 8]
                    end = line.find(quote_char, start + 9)
                    if end != -1:
                        module = line[start + 9:end]
                        imports.append(module)
        
        return imports
    
    def _is_internal_module(self, module: str, current_file: str) -> bool:
        """Check if module is internal to the project."""
        # Skip external/third-party modules
        external_indicators = [
            'numpy', 'pandas', 'requests', 'flask', 'django', 'react', 'vue',
            'express', 'lodash', 'moment', 'os', 'sys', 'json', 're'
        ]
        
        # Check for relative imports
        if module.startswith('.'):
            return True
        
        # Check if it's a known external module
        if any(ext in module.lower() for ext in external_indicators):
            return False
        
        # If module doesn't contain dots, it's likely external
        if '.' not in module and not module.startswith('.'):
            return False
        
        return True
    
    def _detect_cycles(self, dependency_graph: Dict[str, Set[str]]) -> List[Dict[str, Any]]:
        """Detect circular dependencies using DFS."""
        circular_deps = []
        visited = set()
        rec_stack = set()
        
        def dfs(node: str, path: List[str]) -> None:
            if node in rec_stack:
                # Found cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                
                circular_deps.append({
                    "type": "circular_dependency",
                    "pattern": "import_cycle",
                    "severity": self._assess_cycle_severity(cycle),
                    "file": "multiple_modules",
                    "line": None,
                    "message": f"Circular dependency: {' → '.join(cycle)}",
                    "content_preview": f"Cycle: {' → '.join(cycle)}",
                    "metadata": {
                        "cycle": cycle,
                        "cycle_length": len(cycle) - 1,
                        "affected_modules": cycle[:-1]
                    }
                })
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in dependency_graph.get(node, set()):
                dfs(neighbor, path + [node])
            
            rec_stack.remove(node)
        
        # Check each module
        for module in dependency_graph:
            if module not in visited:
                dfs(module, [])
        
        return circular_deps
    
    def _analyze_dependency_patterns(
        self,
        code_results: List[Dict[str, Any]],
        dependency_graph: Dict[str, Set[str]]
    ) -> List[Dict[str, Any]]:
        """Analyze dependency patterns for potential issues."""
        issues = []
        
        # Analyze coupling levels
        for module, dependencies in dependency_graph.items():
            if len(dependencies) > 10:  # High coupling
                issues.append({
                    "type": "dependency_issue",
                    "pattern": "high_coupling",
                    "severity": "medium",
                    "file": module.replace('.', '/') + '.py',
                    "line": 1,
                    "message": f"Module {module} has high coupling ({len(dependencies)} dependencies)",
                    "content_preview": f"Dependencies: {', '.join(list(dependencies)[:5])}...",
                    "metadata": {
                        "dependency_count": len(dependencies),
                        "dependencies": list(dependencies)
                    }
                })
        
        # Find modules that are imported by many others (potential bottlenecks)
        import_counts = {}
        for deps in dependency_graph.values():
            for dep in deps:
                import_counts[dep] = import_counts.get(dep, 0) + 1
        
        for module, count in import_counts.items():
            if count > 8:  # Imported by many modules
                issues.append({
                    "type": "dependency_issue",
                    "pattern": "dependency_bottleneck",
                    "severity": "low",
                    "file": module.replace('.', '/') + '.py',
                    "line": 1,
                    "message": f"Module {module} is imported by {count} other modules",
                    "content_preview": f"Imported by {count} modules",
                    "metadata": {
                        "import_count": count,
                        "potential_bottleneck": True
                    }
                })
        
        return issues
    
    def _assess_cycle_severity(self, cycle: List[str]) -> str:
        """Assess severity of a circular dependency cycle."""
        cycle_length = len(cycle) - 1
        
        if cycle_length <= 2:
            return "high"  # Direct cycles are serious
        elif cycle_length <= 4:
            return "medium"  # Short cycles
        else:
            return "low"  # Long cycles (less immediate impact)
    
    def _assess_circular_deps_severity(self, findings: List[Dict[str, Any]]) -> SeverityLevel:
        """Assess overall circular dependencies severity."""
        if not findings:
            return SeverityLevel.LOW
        
        circular_deps = [f for f in findings if f.get("type") == "circular_dependency"]
        high_coupling = [f for f in findings if f.get("pattern") == "high_coupling"]
        
        if len(circular_deps) > 2:
            return SeverityLevel.CRITICAL
        elif len(circular_deps) > 0:
            return SeverityLevel.HIGH
        elif len(high_coupling) > 3:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW 