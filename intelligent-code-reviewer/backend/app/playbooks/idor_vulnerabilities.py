"""
IDOR Vulnerabilities Detection Playbook.

Specialized playbook for detecting Insecure Direct Object References (IDOR)
and related authorization bypass vulnerabilities.
"""

import re
from typing import Dict, List, Any
from .base_playbook import BasePlaybook
from ..services.ai_agent import AnalysisResult, AnalysisStatus, SeverityLevel, AgentContext


class IdorVulnerabilitiesPlaybook(BasePlaybook):
    """
    Playbook for detecting IDOR vulnerabilities and authorization issues.
    
    Detects:
    - Direct object references without authorization checks
    - Missing access control verification
    - Parameter tampering vulnerabilities
    - Privilege escalation risks
    - Weak object reference patterns
    """
    
    def __init__(self):
        super().__init__(
            name="idor_vulnerabilities",
            description="Detects Insecure Direct Object References and authorization bypass issues",
            version="1.0.0"
        )
        
        # IDOR vulnerability patterns
        self.idor_patterns = {
            "direct_database_access": [
                r"SELECT\s+\*\s+FROM\s+\w+\s+WHERE\s+id\s*=\s*['\"]?\$",
                r"get\w*ById\s*\(\s*\$",
                r"findById\s*\(\s*\$",
                r"Model\.\w+\s*\(\s*\$"
            ],
            "url_parameter_access": [
                r"\$_(GET|POST|REQUEST)\s*\[\s*['\"]id['\"]",
                r"request\.(get|post|params)\s*\[\s*['\"]id['\"]",
                r"params\.(get|id)\s*\(\s*['\"]id['\"]",
                r"req\.params\.id"
            ],
            "file_path_traversal": [
                r"file\s*=\s*\$_(GET|POST|REQUEST)\s*\[",
                r"fopen\s*\(\s*\$_(GET|POST|REQUEST)",
                r"include\s*\(\s*\$_(GET|POST|REQUEST)",
                r"readFile\s*\(\s*req\.(query|params)"
            ],
            "missing_authorization": [
                r"function\s+\w*delete\w*\s*\([^)]*\)\s*{[^}]*(?!.*auth|.*permission|.*check)",
                r"function\s+\w*update\w*\s*\([^)]*\)\s*{[^}]*(?!.*auth|.*permission|.*check)",
                r"@(Delete|Put|Post)Mapping[^{]*{[^}]*(?!.*auth|.*permission|.*check)"
            ]
        }
    
    async def execute(self, context: AgentContext, config: Dict[str, Any] = None) -> AnalysisResult:
        """Execute IDOR vulnerabilities detection analysis."""
        self.logger.info(f"Starting IDOR vulnerabilities analysis for task {context.task_id}")
        
        try:
            search_queries = [
                "database query select by id parameter",
                "user access object reference authorization",
                "request parameter get post id",
                "file access path directory traversal",
                "authentication check permission validation"
            ]
            
            code_results = await self._search_patterns(context, search_queries, max_results=25)
            
            if not code_results:
                return self._create_result(
                    status=AnalysisStatus.COMPLETED,
                    severity=SeverityLevel.LOW,
                    title="IDOR Vulnerabilities Analysis Complete - No Issues Found",
                    description="No IDOR vulnerabilities detected in the codebase.",
                    confidence_score=0.8
                )
            
            idor_findings = []
            
            for result in code_results:
                findings = await self._scan_for_idor_patterns(result)
                idor_findings.extend(findings)
            
            # Analyze authorization patterns
            auth_findings = await self._analyze_authorization_patterns(code_results)
            idor_findings.extend(auth_findings)
            
            overall_severity = self._assess_idor_severity(idor_findings)
            recommendations = self._generate_targeted_recommendations("idor_vulnerability", idor_findings)
            
            return self._create_result(
                status=AnalysisStatus.COMPLETED,
                severity=overall_severity,
                title=f"IDOR Vulnerabilities Analysis Complete - {len(idor_findings)} Issues Found",
                description=f"Detected {len(idor_findings)} potential IDOR vulnerabilities and authorization issues.",
                findings=idor_findings,
                recommendations=recommendations,
                confidence_score=0.85,
                metadata={
                    "playbook_version": self.version,
                    "files_analyzed": len(code_results),
                    "vulnerability_types": self._categorize_idor_findings(idor_findings),
                    "high_risk_issues": len([f for f in idor_findings if f.get("severity") in ["high", "critical"]])
                }
            )
            
        except Exception as e:
            self.logger.error(f"IDOR vulnerabilities analysis failed: {e}")
            return self._create_result(
                status=AnalysisStatus.FAILED,
                severity=SeverityLevel.LOW,
                title="IDOR Vulnerabilities Analysis Failed",
                description=f"Analysis encountered an error: {str(e)}",
                confidence_score=0.0,
                metadata={"error": str(e)}
            )
    
    async def _scan_for_idor_patterns(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scan for IDOR vulnerability patterns."""
        findings = []
        content = result["content"]
        file_path = result["file_path"]
        lines = content.split('\n')
        
        for vuln_type, patterns in self.idor_patterns.items():
            for pattern in patterns:
                try:
                    matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        matched_text = match.group(0)
                        
                        # Check if this is likely a vulnerability
                        if self._is_likely_vulnerability(content, match.start(), vuln_type):
                            findings.append({
                                "type": "idor_vulnerability",
                                "pattern": vuln_type,
                                "severity": self._get_idor_severity(vuln_type),
                                "file": file_path,
                                "line": line_num,
                                "message": self._generate_idor_message(vuln_type, matched_text),
                                "content_preview": matched_text.strip()[:100],
                                "metadata": {
                                    "vulnerability_type": vuln_type,
                                    "pattern_matched": pattern,
                                    "context": self._extract_context(lines, line_num),
                                    "risk_level": self._assess_risk_level(vuln_type, content)
                                }
                            })
                except re.error:
                    continue
        
        return findings
    
    async def _analyze_authorization_patterns(self, code_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze authorization and access control patterns."""
        findings = []
        
        # Look for endpoints/functions that modify data without authorization checks
        for result in code_results:
            content = result["content"]
            file_path = result["file_path"]
            
            # Check for API endpoints
            api_endpoints = self._find_api_endpoints(content)
            
            for endpoint in api_endpoints:
                if self._is_sensitive_operation(endpoint) and not self._has_authorization_check(endpoint["content"]):
                    findings.append({
                        "type": "idor_vulnerability",
                        "pattern": "missing_authorization_check",
                        "severity": "high",
                        "file": file_path,
                        "line": endpoint["line"],
                        "message": f"Sensitive operation '{endpoint['name']}' lacks authorization check",
                        "content_preview": endpoint["content"][:100],
                        "metadata": {
                            "endpoint_type": endpoint["type"],
                            "operation": endpoint["name"],
                            "missing_check": "authorization"
                        }
                    })
        
        return findings
    
    def _is_likely_vulnerability(self, content: str, match_start: int, vuln_type: str) -> bool:
        """Check if the matched pattern is likely a real vulnerability."""
        # Extract surrounding context
        context_start = max(0, match_start - 200)
        context_end = min(len(content), match_start + 200)
        context = content[context_start:context_end]
        
        # Look for mitigating factors
        mitigation_keywords = [
            "auth", "permission", "authorize", "check", "validate", "verify",
            "current_user", "user_id", "owner", "access_control", "acl"
        ]
        
        # If we find authorization keywords nearby, it's less likely to be vulnerable
        if any(keyword in context.lower() for keyword in mitigation_keywords):
            return False
        
        # Type-specific checks
        if vuln_type == "direct_database_access":
            # Check if there's any filtering beyond just ID
            if "current_user" in context or "user_id" in context:
                return False
        
        elif vuln_type == "missing_authorization":
            # Already checked for auth keywords above
            pass
        
        return True
    
    def _find_api_endpoints(self, content: str) -> List[Dict[str, Any]]:
        """Find API endpoints in the code."""
        endpoints = []
        lines = content.split('\n')
        
        # Common API endpoint patterns
        endpoint_patterns = [
            (r'@(Get|Post|Put|Delete)Mapping\s*\([^)]*\)', 'spring'),
            (r'@app\.route\s*\([^)]*\)', 'flask'),
            (r'router\.(get|post|put|delete)\s*\([^)]*\)', 'express'),
            (r'def\s+(get|post|put|delete)_\w+\s*\(', 'function')
        ]
        
        for i, line in enumerate(lines):
            for pattern, endpoint_type in endpoint_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    # Extract function/method content (simplified)
                    endpoint_content = self._extract_function_content(lines, i)
                    
                    endpoints.append({
                        "line": i + 1,
                        "type": endpoint_type,
                        "name": match.group(0),
                        "content": endpoint_content
                    })
        
        return endpoints
    
    def _extract_function_content(self, lines: List[str], start_line: int) -> str:
        """Extract function content starting from a line."""
        content_lines = []
        brace_count = 0
        indent_level = None
        
        for i in range(start_line, min(len(lines), start_line + 50)):  # Limit to 50 lines
            line = lines[i]
            
            if indent_level is None and line.strip():
                indent_level = len(line) - len(line.lstrip())
            
            # Simple brace counting for languages like Java/JavaScript
            brace_count += line.count('{') - line.count('}')
            content_lines.append(line)
            
            # Stop if we've closed all braces or returned to original indent level
            if brace_count == 0 and i > start_line:
                break
            elif indent_level is not None and line.strip():
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= indent_level and i > start_line and not line.strip().startswith((')', '}', ']')):
                    break
        
        return '\n'.join(content_lines)
    
    def _is_sensitive_operation(self, endpoint: Dict[str, Any]) -> bool:
        """Check if endpoint performs sensitive operations."""
        sensitive_keywords = [
            'delete', 'remove', 'update', 'modify', 'edit', 'change',
            'create', 'add', 'insert', 'save', 'write'
        ]
        
        name_lower = endpoint["name"].lower()
        content_lower = endpoint["content"].lower()
        
        return any(keyword in name_lower or keyword in content_lower for keyword in sensitive_keywords)
    
    def _has_authorization_check(self, content: str) -> bool:
        """Check if content has authorization checks."""
        auth_keywords = [
            'authorize', 'permission', 'access_control', 'check_permission',
            'current_user', 'authenticated', 'login_required', 'require_auth',
            'verify_user', 'check_owner', 'user_can', 'has_permission'
        ]
        
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in auth_keywords)
    
    def _extract_context(self, lines: List[str], line_num: int) -> str:
        """Extract context around a line."""
        start = max(0, line_num - 3)
        end = min(len(lines), line_num + 2)
        return '\n'.join(lines[start:end])
    
    def _get_idor_severity(self, vuln_type: str) -> str:
        """Get severity level for IDOR vulnerability types."""
        high_risk = ["direct_database_access", "missing_authorization"]
        medium_risk = ["url_parameter_access", "file_path_traversal"]
        
        if vuln_type in high_risk:
            return "high"
        elif vuln_type in medium_risk:
            return "medium"
        else:
            return "low"
    
    def _generate_idor_message(self, vuln_type: str, matched_text: str) -> str:
        """Generate descriptive message for IDOR finding."""
        messages = {
            "direct_database_access": "Direct database access without authorization check",
            "url_parameter_access": "URL parameter used without validation",
            "file_path_traversal": "File access using user input without validation",
            "missing_authorization": "Sensitive operation without authorization check"
        }
        
        return messages.get(vuln_type, f"Potential IDOR vulnerability: {vuln_type}")
    
    def _assess_risk_level(self, vuln_type: str, content: str) -> str:
        """Assess risk level based on vulnerability type and context."""
        # Check for additional risk factors
        risk_factors = []
        
        content_lower = content.lower()
        
        if 'admin' in content_lower or 'root' in content_lower:
            risk_factors.append("admin_functionality")
        
        if 'delete' in content_lower or 'remove' in content_lower:
            risk_factors.append("destructive_operation")
        
        if 'payment' in content_lower or 'financial' in content_lower:
            risk_factors.append("financial_data")
        
        if len(risk_factors) > 1:
            return "critical"
        elif len(risk_factors) > 0:
            return "high"
        else:
            return "medium"
    
    def _categorize_idor_findings(self, findings: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize IDOR findings by type."""
        categories = {}
        for finding in findings:
            vuln_type = finding.get("pattern", "unknown")
            categories[vuln_type] = categories.get(vuln_type, 0) + 1
        return categories
    
    def _assess_idor_severity(self, findings: List[Dict[str, Any]]) -> SeverityLevel:
        """Assess overall IDOR severity."""
        if not findings:
            return SeverityLevel.LOW
        
        critical_count = len([f for f in findings if f.get("severity") == "critical"])
        high_count = len([f for f in findings if f.get("severity") == "high"])
        
        # IDOR vulnerabilities are serious security issues
        if critical_count > 0:
            return SeverityLevel.CRITICAL
        elif high_count > 1:
            return SeverityLevel.HIGH
        elif high_count > 0 or len(findings) > 3:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW 