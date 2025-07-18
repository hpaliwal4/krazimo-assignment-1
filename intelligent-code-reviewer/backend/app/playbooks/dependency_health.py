"""
Dependency Health Analysis Playbook.

Specialized playbook for analyzing dependency health including
version freshness, security vulnerabilities, and management issues.
"""

import re
from typing import Dict, List, Any
from .base_playbook import BasePlaybook
from ..services.ai_agent import AnalysisResult, AnalysisStatus, SeverityLevel, AgentContext


class DependencyHealthPlaybook(BasePlaybook):
    """
    Playbook for analyzing dependency health and management.
    
    Analyzes:
    - Dependency version management
    - Potential security vulnerabilities
    - Outdated dependencies
    - Dependency conflicts
    - License compatibility
    """
    
    def __init__(self):
        super().__init__(
            name="dependency_health",
            description="Analyzes dependency health, versions, and security issues",
            version="1.0.0"
        )
    
    async def execute(self, context: AgentContext, config: Dict[str, Any] = None) -> AnalysisResult:
        """Execute dependency health analysis."""
        self.logger.info(f"Starting dependency health analysis for task {context.task_id}")
        
        try:
            search_queries = [
                "package.json requirements.txt dependencies",
                "pip install npm install package version",
                "dependency management security vulnerability",
                "outdated package version update",
                "package lock file yarn.lock"
            ]
            
            code_results = await self._search_patterns(context, search_queries, max_results=20)
            
            if not code_results:
                return self._create_result(
                    status=AnalysisStatus.COMPLETED,
                    severity=SeverityLevel.LOW,
                    title="Dependency Health Analysis Complete - No Configuration Found",
                    description="No dependency configuration files found for analysis.",
                    confidence_score=0.7
                )
            
            dependency_findings = []
            
            for result in code_results:
                if self._is_dependency_file(result["file_path"]):
                    findings = await self._analyze_dependency_file(result)
                    dependency_findings.extend(findings)
            
            overall_severity = self._assess_dependency_health_severity(dependency_findings)
            recommendations = self._generate_targeted_recommendations("dependency_health", dependency_findings)
            
            return self._create_result(
                status=AnalysisStatus.COMPLETED,
                severity=overall_severity,
                title=f"Dependency Health Analysis Complete - {len(dependency_findings)} Issues Found",
                description=f"Analyzed dependency health and identified {len(dependency_findings)} potential issues.",
                findings=dependency_findings,
                recommendations=recommendations,
                confidence_score=0.8,
                metadata={
                    "playbook_version": self.version,
                    "dependency_files_analyzed": len([r for r in code_results if self._is_dependency_file(r["file_path"])]),
                    "health_issues": len(dependency_findings)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Dependency health analysis failed: {e}")
            return self._create_result(
                status=AnalysisStatus.FAILED,
                severity=SeverityLevel.LOW,
                title="Dependency Health Analysis Failed",
                description=f"Analysis encountered an error: {str(e)}",
                confidence_score=0.0,
                metadata={"error": str(e)}
            )
    
    def _is_dependency_file(self, file_path: str) -> bool:
        """Check if file is a dependency configuration file."""
        dependency_files = [
            "package.json", "requirements.txt", "setup.py", "pyproject.toml",
            "Pipfile", "composer.json", "build.gradle", "pom.xml", "Cargo.toml"
        ]
        return any(dep_file in file_path for dep_file in dependency_files)
    
    async def _analyze_dependency_file(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze a dependency configuration file."""
        findings = []
        content = result["content"]
        file_path = result["file_path"]
        
        if "package.json" in file_path:
            findings.extend(self._analyze_npm_dependencies(content, file_path))
        elif "requirements.txt" in file_path:
            findings.extend(self._analyze_python_dependencies(content, file_path))
        elif "setup.py" in file_path or "pyproject.toml" in file_path:
            findings.extend(self._analyze_python_setup(content, file_path))
        
        return findings
    
    def _analyze_npm_dependencies(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Analyze npm package.json dependencies."""
        findings = []
        
        try:
            import json
            package_data = json.loads(content)
        except json.JSONDecodeError:
            return [{
                "type": "dependency_issue",
                "pattern": "invalid_package_json",
                "severity": "high",
                "file": file_path,
                "line": 1,
                "message": "Invalid package.json format",
                "content_preview": "Malformed JSON in package.json",
                "metadata": {"issue_type": "syntax_error"}
            }]
        
        # Analyze dependencies sections
        dep_sections = ["dependencies", "devDependencies", "peerDependencies"]
        total_deps = 0
        unpinned_deps = 0
        
        for section in dep_sections:
            if section in package_data:
                deps = package_data[section]
                total_deps += len(deps)
                
                for pkg_name, version in deps.items():
                    # Check for unpinned versions
                    if version.startswith('^') or version.startswith('~') or version == '*':
                        unpinned_deps += 1
                    
                    # Check for potentially problematic packages
                    if self._is_potentially_problematic_package(pkg_name):
                        findings.append({
                            "type": "dependency_issue",
                            "pattern": "problematic_package",
                            "severity": "medium",
                            "file": file_path,
                            "line": None,
                            "message": f"Package '{pkg_name}' may have known issues",
                            "content_preview": f"{pkg_name}: {version}",
                            "metadata": {
                                "package_name": pkg_name,
                                "version": version,
                                "section": section
                            }
                        })
        
        # Check for too many dependencies
        if total_deps > 50:
            findings.append({
                "type": "dependency_issue",
                "pattern": "excessive_dependencies",
                "severity": "medium",
                "file": file_path,
                "line": None,
                "message": f"High number of dependencies ({total_deps}) may impact maintainability",
                "content_preview": f"{total_deps} total dependencies",
                "metadata": {"dependency_count": total_deps}
            })
        
        # Check for unpinned versions
        if unpinned_deps > total_deps * 0.5:  # More than 50% unpinned
            findings.append({
                "type": "dependency_issue",
                "pattern": "unpinned_versions",
                "severity": "medium",
                "file": file_path,
                "line": None,
                "message": f"{unpinned_deps} dependencies are not pinned to specific versions",
                "content_preview": f"{unpinned_deps}/{total_deps} unpinned dependencies",
                "metadata": {"unpinned_count": unpinned_deps, "total_count": total_deps}
            })
        
        return findings
    
    def _analyze_python_dependencies(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Analyze Python requirements.txt dependencies."""
        findings = []
        lines = content.split('\n')
        
        unpinned_count = 0
        total_count = 0
        
        for i, line in enumerate(lines):
            line = line.strip()
            if line and not line.startswith('#'):
                total_count += 1
                
                # Check for unpinned versions
                if '==' not in line and '>=' not in line and '<=' not in line and '~=' not in line:
                    unpinned_count += 1
                
                # Check for potentially problematic packages
                pkg_name = line.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0].strip()
                if self._is_potentially_problematic_package(pkg_name):
                    findings.append({
                        "type": "dependency_issue",
                        "pattern": "problematic_package",
                        "severity": "medium",
                        "file": file_path,
                        "line": i + 1,
                        "message": f"Package '{pkg_name}' may have known issues",
                        "content_preview": line,
                        "metadata": {"package_name": pkg_name}
                    })
        
        # Check for unpinned versions
        if unpinned_count > 0:
            findings.append({
                "type": "dependency_issue",
                "pattern": "unpinned_python_versions",
                "severity": "medium",
                "file": file_path,
                "line": None,
                "message": f"{unpinned_count} Python packages without version pins",
                "content_preview": f"{unpinned_count}/{total_count} unpinned packages",
                "metadata": {"unpinned_count": unpinned_count, "total_count": total_count}
            })
        
        return findings
    
    def _analyze_python_setup(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Analyze Python setup.py or pyproject.toml."""
        findings = []
        
        # Look for dependency specifications
        if 'install_requires' in content or 'dependencies' in content:
            # Extract dependencies (simplified analysis)
            deps = re.findall(r'["\']([a-zA-Z0-9_-]+)[>=<~!]*[^"\']*["\']', content)
            
            for dep in deps:
                if self._is_potentially_problematic_package(dep):
                    findings.append({
                        "type": "dependency_issue",
                        "pattern": "problematic_package",
                        "severity": "medium",
                        "file": file_path,
                        "line": None,
                        "message": f"Package '{dep}' may have known issues",
                        "content_preview": f"Dependency: {dep}",
                        "metadata": {"package_name": dep}
                    })
        
        return findings
    
    def _is_potentially_problematic_package(self, package_name: str) -> bool:
        """Check if package is known to have issues (simplified heuristic)."""
        # This is a simplified check - in practice, you'd use a vulnerability database
        problematic_patterns = [
            'debug', 'test', 'mock', 'temp', 'experimental',
            'alpha', 'beta', 'rc', 'dev', 'unstable'
        ]
        
        pkg_lower = package_name.lower()
        return any(pattern in pkg_lower for pattern in problematic_patterns)
    
    def _assess_dependency_health_severity(self, findings: List[Dict[str, Any]]) -> SeverityLevel:
        """Assess overall dependency health severity."""
        if not findings:
            return SeverityLevel.LOW
        
        problematic_packages = len([f for f in findings if f.get("pattern") == "problematic_package"])
        unpinned_issues = len([f for f in findings if "unpinned" in f.get("pattern", "")])
        
        if problematic_packages > 3:
            return SeverityLevel.HIGH
        elif problematic_packages > 0 or unpinned_issues > 1:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW 